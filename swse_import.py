#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
swse_import.py — Importa Opponents SWSE (Heroic/Nonheroic/Beast/General/Droid)
nel Vault Obsidian per Fantasy Statblocks (layout: "SWSE Creature").

Correzioni incluse:
- Campi puliti dal markup wiki (''' e [[link]]).
- Perception separata da Senses e mai forzata dentro Senses.
- HP e Damage Threshold separati anche se sulla stessa riga.
- Melee/Ranged come array di voci singole, non stringa unica.
- Abilities sia come stringa normalizzata ("Str 10; Dex 12; ...")
  sia come oggetto `stats` {Str, Dex, Con, Int, Wis, Cha} per la tabella del layout.
- Frontmatter compatibile con il layout fornito e con autoParse.
"""
import os
import re
import sys
import time
import json
import hashlib
import argparse
from datetime import datetime, timezone
import requests

try:
    import mwparserfromhell
except ImportError:
    sys.stderr.write("Errore: manca mwparserfromhell. Esegui: pip install mwparserfromhell requests\n")
    sys.exit(1)

API_URL = "https://swse.fandom.com/api.php"

# Categorie Opponents (MediaWiki)
OPPONENT_CATEGORIES = {
    "Heroic":   "Category:Heroic Units",
    "Nonheroic":"Category:Nonheroic Units",
    "Beast":    "Category:Beasts",
    "General":  "Category:General Units",
    "Droid":    "Category:Droids"
}

ENTITY_CONFIG = {
    # altre entità lasciate per compatibilità, non necessarie al bestiario
    'opponents': {'category': list(OPPONENT_CATEGORIES.values()), 'out_dir': '05_Bestiario'}
}

# ---------- UTIL ----------
def title_to_slug(title: str) -> str:
    slug = title.strip().lower()
    slug = slug.replace('/', ' ')
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    return slug

def safe_filename(name: str) -> str:
    name = name.replace('/', '∕').replace('\\', '∖').replace(':', '·')
    name = name.replace('*', '×').replace('?', '¿').replace('"', "'")
    name = name.replace('<', '‹').replace('>', '›').replace('|', '¦')
    return name

def api_get(params):
    retries = 4
    for i in range(retries):
        try:
            r = requests.get(API_URL, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            sys.stderr.write(f"API error {i+1}/{retries}: {e}\n")
        time.sleep(1.0 + i * 0.8)
    return None

def iso_now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def build_slug_index(vault_path: str) -> dict:
    index = {}
    vp = os.path.abspath(vault_path)
    for root, _, files in os.walk(vp):
        for fn in files:
            if fn.lower().endswith(".md"):
                slug = os.path.splitext(fn)[0]
                rel = os.path.relpath(os.path.join(root, fn), vp)
                index[slug] = rel.replace("\\", "/")
    return index

def make_link_resolver(vault_path: str, slug_index: dict):
    def resolver(page_title: str, anchor: str | None, label: str | None) -> str:
        if page_title.startswith(("Category:", "File:", "Image:", "Template:")):
            return ""
        page_title = page_title.strip()
        alias = (label or page_title).strip()
        slug = title_to_slug(page_title)
        if slug in slug_index:
            target = slug_index[slug]
            if anchor:
                target = f"{target}#{anchor}"
            return f"[[{target}|{alias}]]"
        url = f"https://swse.fandom.com/wiki/{page_title.replace(' ', '_')}"
        if anchor:
            url += f"#{anchor.replace(' ', '_')}"
        return f"[{alias}]({url})"
    return resolver

def clean_text(txt: str) -> str:
    if not txt:
        return ""
    s = mwparserfromhell.parse(txt).strip_code()
    s = re.sub(r"'{2,3}", "", s)   # rimuovi '' e '''
    s = re.sub(r"\s+", " ", s).strip(" \t,;")
    return s

def split_list(s: str) -> list[str]:
    if not s:
        return []
    # privilegia ';' come separatore; altrimenti spezza su virgola non seguita da numero negativo
    parts = re.split(r';\s*', s)
    if len(parts) == 1:
        parts = re.split(r',\s*(?=[A-Z0-9(])', s)
    out = [clean_text(p) for p in parts if clean_text(p)]
    return out

def explode_attacks(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines or []:
        # una riga "Melee: A; B; C" -> tre voci
        parts = re.split(r'\s*;\s*', ln)
        for p in parts:
            p = clean_text(p)
            if p:
                out.append(p)
    return out

def parse_stats(abilities_text: str) -> tuple[str, dict]:
    """
    Ritorna:
      - abilities_str: "Str 10; Dex 12; Con -; Int 14; Wis 13; Cha 14"
      - stats_obj:     {"Str": 10, "Dex": 12, "Con": null, "Int": 14, "Wis": 13, "Cha": 14}
    Accetta sia forme estese (Strength, Dexterity...) sia abbreviazioni.
    """
    cleaned = clean_text(abilities_text)
    if not cleaned:
        return "", {"Str": None, "Dex": None, "Con": None, "Int": None, "Wis": None, "Cha": None}

    # normalizza nomi lunghi in brevi
    rep = {
        r'\bStrength\b': 'Str', r'\bDexterity\b': 'Dex', r'\bConstitution\b': 'Con',
        r'\bIntelligence\b': 'Int', r'\bWisdom\b': 'Wis', r'\bCharisma\b': 'Cha'
    }
    for pat, repl in rep.items():
        cleaned = re.sub(pat, repl, cleaned, flags=re.IGNORECASE)

    # estrai coppie Abbrev +/-numero o "-"
    stats = {"Str": None, "Dex": None, "Con": None, "Int": None, "Wis": None, "Cha": None}
    for key in list(stats.keys()):
        m = re.search(rf'\b{key}\b\s*([+\-]?\d+|—|-)', cleaned, flags=re.IGNORECASE)
        if m:
            val = m.group(1)
            if val in ('-', '—'):
                stats[key] = None
            else:
                try:
                    stats[key] = int(val)
                except ValueError:
                    stats[key] = None

    # ricostruisci stringa normalizzata ordinata
    seq = [f"{k} {stats[k] if stats[k] is not None else '-'}" for k in ["Str","Dex","Con","Int","Wis","Cha"]]
    abilities_str = "; ".join(seq)
    return abilities_str, stats

# ---------- FETCH ----------
def fetch_category_members(cats, limit=0):
    cats = cats if isinstance(cats, list) else [cats]
    members, seen = [], set()
    for cat in cats:
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': cat,
            'cmlimit': 'max',
            'format': 'json'
        }
        while True:
            res = api_get(params)
            if not res or 'error' in res:
                break
            batch = res.get('query', {}).get('categorymembers', [])
            for m in batch:
                pid = m.get('pageid')
                if pid in seen:
                    continue
                seen.add(pid)
                members.append(m)
                if limit and len(members) >= limit:
                    return members
            cont = res.get('continue') or res.get('query-continue', {})
            if cont and 'cmcontinue' in cont:
                params['cmcontinue'] = cont['cmcontinue']
            else:
                break
    return members

# ---------- PARSER OPPONENTS ----------
_HDR_RE = re.compile(r'==+\s*(?P<name>[^=\n]+?)\s+Statistics\s*\(CL\s*(?P<cl>\d+)\s*\)\s*==+', re.IGNORECASE)

def _grab_first(regex, text):
    m = regex.search(text)
    return m.group(1).strip() if m else ""

def _grab_all_lines(prefix, text):
    patt = re.compile(rf'^{prefix}\s*:\s*(.+)$', re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in patt.findall(text)]

def parse_opponent_sections(page_title: str, wikitext: str) -> list[dict]:
    res = []
    headers = [(m.start(), m.end(), m.group('name').strip(), int(m.group('cl'))) for m in _HDR_RE.finditer(wikitext)]
    if not headers:
        mcl = re.search(r'\bCL\s*(\d{1,2})\b', wikitext, re.IGNORECASE)
        cl = int(mcl.group(1)) if mcl else None
        block = extract_fields_from_block(page_title, cl, wikitext)
        if block:
            res.append(block)
        return res

    for i, (s, e, nm, cl) in enumerate(headers):
        body_start = e
        body_end = headers[i+1][0] if i+1 < len(headers) else len(wikitext)
        section_text = wikitext[body_start:body_end]
        blk = extract_fields_from_block(nm, cl, section_text)
        if blk:
            res.append(blk)
    return res

def extract_fields_from_block(name_guess: str, cl_guess: int | None, text: str) -> dict:
    t = text

    # riga tipo (taglia/tipo/livelli) = prima riga utile non di intestazione/campi
    type_line = ""
    for ln in t.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(('{|','!','|-','|}')):
            continue
        if re.match(r'^(?:' + "|".join([
            'Initiative','Senses','Perception','Languages','Reflex','Fortitude','Will',
            'Hit Points','HP','Damage Threshold','Speed','Melee','Ranged','Attack Options',
            'Special Actions','Talents','Feats','Skills','Force Power Suite','Possessions',
            'Equipment','Weapons','Abilities','Immune','Special Qualities','Species Traits'
        ]) + r')\s*:?', ln, re.IGNORECASE):
            break
        type_line = ln
        break

    name = name_guess.strip() or "Unknown"
    cl = cl_guess
    if cl is None:
        mcl = re.search(r'\bCL\s*(\d{1,2})\b', t, re.IGNORECASE)
        cl = int(mcl.group(1)) if mcl else None

    # Initiative
    initiative = _grab_first(re.compile(r"\bInitiative\s*:\s*([^\n]+)", re.IGNORECASE), t)
    initiative = clean_text(initiative)

    # Senses + Perception
    senses_raw = _grab_first(re.compile(r"\bSenses\s*:?\s*([^\n]+)", re.IGNORECASE), t)
    perception_num = None

    if senses_raw:
        m = re.search(r'Perception\s*\+?(-?\d+)', senses_raw, re.IGNORECASE)
        if m:
            perception_num = m.group(1)
            senses_raw = re.sub(r'[,;]?\s*Perception\s*\+?-?\d+', '', senses_raw, flags=re.IGNORECASE)

    if perception_num is None:
        m = re.search(r"^\s*'{0,3}\s*Perception\s*\+?(-?\d+)\s*$", t, re.IGNORECASE | re.MULTILINE)
        if m:
            perception_num = m.group(1)
            senses_raw = ""

    senses = clean_text(senses_raw)
    perception = ""
    if perception_num is not None:
        perception = perception_num if str(perception_num).startswith(("+","-")) else f"+{perception_num}"

    # Defenses
    defense_any = clean_text(_grab_first(re.compile(r"\bDefen(?:s|c)es?\s*:?\s*([^\n]+)", re.IGNORECASE), t))

    def grab_def(name):
        # prova "Reflex: ..." oppure "Reflex ..." ovunque
        m = re.search(rf"\b{name}(?:\s*Defense)?\s*:?\s*([0-9][^,;\n]*)", t, re.IGNORECASE)
        if m: return clean_text(m.group(1))
        if defense_any:
            m = re.search(rf"\b{name}\b(?:\s*Defense)?\s*([0-9][^,;]*)", defense_any, re.IGNORECASE)
            if m: return clean_text(m.group(1))
        return ""

    reflex    = grab_def("Reflex")
    fortitude = grab_def("Fortitude")
    will      = grab_def("Will")

    # HP e Threshold (anche su stessa riga)
    hp_line        = _grab_first(re.compile(r"\b(?:Hit Points?|HP)\s*:?\s*([^\n]+)", re.IGNORECASE), t)
    threshold_line = _grab_first(re.compile(r"\bDamage Threshold\s*:?\s*([^\n]+)", re.IGNORECASE), t)

    def extract_first_int(s: str):
        if not s: return ""
        m = re.search(r'(-?\d+)', s)
        return int(m.group(1)) if m else ""

    hp = extract_first_int(hp_line)
    threshold = extract_first_int(threshold_line)
    # se hp_line contiene anche "Damage Threshold: N", rimuovi per sicurezza dal testo hp
    # (ma noi usiamo int, quindi non serve oltre a pulizia)

    # Speed
    speed = clean_text(_grab_first(re.compile(r"\bSpeed\s*:?\s*([^\n]+)", re.IGNORECASE), t))

    # Attacks
    melee_lines = _grab_all_lines("Melee", t)
    ranged_lines = _grab_all_lines("Ranged", t)
    melee = explode_attacks(melee_lines)
    ranged = explode_attacks(ranged_lines)

    # Options / Actions
    attack_opts     = clean_text(_grab_first(re.compile(r"\bAttack Options\s*:?\s*([^\n]+)", re.IGNORECASE), t))
    special_actions = clean_text(_grab_first(re.compile(r"\bSpecial Actions\s*:?\s*([^\n]+)", re.IGNORECASE), t))

    # Lists
    talents = split_list(_grab_first(re.compile(r"\bTalents\s*:\s*([^\n]+)", re.IGNORECASE), t))
    feats = split_list(_grab_first(re.compile(r"\bFeats\s*:\s*([^\n]+)", re.IGNORECASE), t))
    skills = split_list(_grab_first(re.compile(r"\bSkills\s*:\s*([^\n]+)", re.IGNORECASE), t))
    special_qualities = split_list(
        _grab_first(re.compile(r"(?:Special Qualities|Species Traits)\s*:\s*([^\n]+)", re.IGNORECASE), t)
    )

    # Force
    m_utf = re.search(r"\bUse the Force\s*\+(-?\d+)", t, re.IGNORECASE)
    use_the_force = f"+{m_utf.group(1)}" if m_utf else ""
    fps_line = _grab_first(re.compile(r"Force Power Suite[^\n]*:\s*([^\n]+)", re.IGNORECASE), t)
    force_powers = split_list(re.sub(r'^\([^)]*\)\s*', '', fps_line)) if fps_line else []

    # Equipment / Possessions
    eq_line = _grab_first(re.compile(r"(?:Possessions|Equipment|Weapons)\s*:\s*([^\n]+)", re.IGNORECASE), t)
    equipment = split_list(eq_line)

    # Abilities -> abilities string + stats object
    abil_raw = _grab_first(re.compile(r"\bAbilities\s*:\s*([^\n]+)", re.IGNORECASE), t)
    abilities_str, stats_obj = parse_stats(abil_raw)

    # Languages
    languages = clean_text(_grab_first(re.compile(r"\bLanguages\s*:\s*([^\n]+)", re.IGNORECASE), t))

    # Notes
    notes = []
    for ln in t.splitlines():
        lns = ln.strip()
        if lns.startswith('*') or ('—' in lns and not re.match(r"^=+", lns)):
            clean = clean_text(lns)
            if clean and not re.match(r"^\*+\s*(?:See|Source|Reference)", clean, re.IGNORECASE):
                notes.append(clean)
    notes = " ".join(notes) if notes else ""

    # Source
    m_source = re.search(r"Reference Book\s*:\s*([^\n(]+)", t, re.IGNORECASE)
    source_book = clean_text(m_source.group(1)) if m_source else ""
    # type line pulito
    type_line_clean = clean_text(type_line)

    return {
        'name': name,
        'type_line': type_line_clean,
        'cl': int(cl) if isinstance(cl, int) or (isinstance(cl, str) and cl.isdigit()) else "",
        'initiative': initiative,
        'senses': senses,
        'perception': perception,
        'reflex': reflex,
        'fortitude': fortitude,
        'will': will,
        'hp': hp,
        'threshold': threshold,
        'speed': speed,
        'melee': melee,
        'ranged': ranged,
        'attackOptions': attack_opts,
        'specialActions': special_actions,
        'specialQualities': special_qualities,
        'talents': talents,
        'feats': feats,
        'skills': skills,
        'useTheForce': use_the_force,
        'forcePowers': force_powers,
        'equipment': equipment,
        'abilities': abilities_str,
        'stats': stats_obj,
        'languages': languages,
        'notes': notes,
        'source_book': source_book
    }

# ---------- YAML / WRITE ----------
def dump_frontmatter(frontmatter: dict) -> str:
    def dump_val(v, indent=0):
        if isinstance(v, list):
            if not v:
                return "[]"
            return "[{}]".format(", ".join(_yaml_escape(x) for x in v))
        elif isinstance(v, dict):
            lines = []
            for kk, vv in v.items():
                if isinstance(vv, (list, dict)) or "\n" in str(vv):
                    lines.append(" " * indent + f"{kk}:")
                    sub = dump_val(vv, indent + 2)
                    if "\n" in sub:
                        lines.append(sub)
                    else:
                        lines.append(" " * (indent + 2) + sub)
                else:
                    lines.append(" " * indent + f"{kk}: {_yaml_escape(vv)}")
            return "\n".join(lines)
        else:
            s = str(v)
            if "\n" in s:
                return "|\n" + "\n".join("  " + ln for ln in s.splitlines())
            return _yaml_escape(s)

    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, (list, dict)) or "\n" in str(v):
            if isinstance(v, dict):
                lines.append(f"{k}:")
                sub = dump_val(v, 2)
                lines.append(sub)
            else:
                lines.append(f"{k}: {dump_val(v)}")
        else:
            lines.append(f"{k}: {_yaml_escape(v)}")
    lines.append("---")
    return "\n".join(lines)

def _yaml_escape(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    s = str(v)
    if s == "" or any(ch in s for ch in [":", "-", "[", "]", "{", "}", "#", ",", '"', "'"]):
        s = s.replace('"', '\\"')
        return f"\"{s}\""
    return s

# ---------- IMPORT CORE ----------
def infer_unit_kind(kind_hint: str | None, blk: dict) -> str:
    if kind_hint in {"Heroic","Nonheroic","Beast","General","Droid"}:
        return kind_hint
    tl = (blk.get('type_line') or "").lower()
    nm = (blk.get('name') or "").lower()
    if "droid" in tl or "droid" in nm:
        return "Droid"
    if "beast" in tl:
        return "Beast"
    if "nonheroic" in tl:
        return "Nonheroic"
    if any(k in tl for k in ["soldier","scout","noble","scoundrel","jedi","ace pilot","bounty hunter"]):
        return "Heroic"
    return "General"

def import_entity(entity, vault_path, limit=0, dry_run=False, force=False):
    if entity not in ENTITY_CONFIG:
        print(f"Entità '{entity}' non supportata.")
        return

    cfg = ENTITY_CONFIG[entity]
    out_dir = os.path.join(vault_path, cfg['out_dir'])
    os.makedirs(out_dir, exist_ok=True)

    log_file = os.path.join(vault_path, "98_Imports_SWSE", "import.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logf = open(log_file, "a", encoding="utf-8")

    slug_index = build_slug_index(vault_path)
    link_resolver = make_link_resolver(vault_path, slug_index)

    # raccolta pagine opponents
    members = []
    for tlabel, cat in OPPONENT_CATEGORIES.items():
        ms = fetch_category_members(cat, limit=0 if not limit else max(1, limit - len(members)))
        for m in ms:
            m = dict(m)
            m['__unit_kind'] = tlabel
            members.append(m)
        if limit and len(members) >= limit:
            members = members[:limit]
            break
    # dedup con priorità
    priority = {"Heroic":5, "Nonheroic":4, "Beast":3, "Droid":2, "General":1}
    dedup = {}
    for m in members:
        pid = m.get('pageid')
        if pid not in dedup or priority[m['__unit_kind']] > priority[dedup[pid]['__unit_kind']]:
            dedup[pid] = m
    members = list(dedup.values())

    if not members:
        print(f"Nessun risultato in {cfg['category']}")
        return
    print(f"Trovate {len(members)} pagine Opponents.")

    count = 0
    for mem in members:
        title = mem['title']
        unit_kind_hint = mem.get('__unit_kind')
        count += 1
        if limit and count > limit:
            break

        # wikitext
        params = {
            'action': 'query',
            'prop': 'revisions',
            'rvslots': 'main',
            'rvprop': 'content',
            'titles': title,
            'format': 'json'
        }
        data = api_get(params)
        if not data:
            print(f"Impossibile recuperare {title}.")
            logf.write(f"ERROR: fetch {title}\n")
            continue
        page = next(iter(data['query']['pages'].values()))
        if 'revisions' not in page:
            print(f"Pagina {title} senza contenuto.")
            logf.write(f"WARN: no content {title}\n")
            continue
        wikitext = page['revisions'][0]['slots']['main']['*']

        blocks = parse_opponent_sections(title, wikitext)
        if not blocks:
            print(f"WARN: nessun statblock trovato in '{title}'.")
            logf.write(f"WARN: no statblock {title}\n")
            continue

        for blk in blocks:
            name = blk['name']
            cl_int = int(blk['cl']) if str(blk['cl']).isdigit() else 0
            logical_type = infer_unit_kind(unit_kind_hint, blk)

            # payload per hash e frontmatter
            payload = {
                k: blk[k] for k in [
                    'name','type_line','cl','initiative','senses','perception','reflex','fortitude','will',
                    'hp','threshold','speed','melee','ranged','attackOptions','specialActions',
                    'specialQualities','talents','feats','skills','useTheForce','forcePowers',
                    'equipment','abilities','stats','languages','notes','source_book'
                ]
            }
            hash_val = hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

            fname = f"CL{cl_int:02d} - {safe_filename(name)}.md"
            filename = os.path.join(out_dir, fname)
            exists = os.path.isfile(filename)
            if exists and not force:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                m = re.search(r"import_hash:\s*([0-9a-fA-F]+)", content)
                old_hash = m.group(1) if m else ""
                if old_hash == hash_val:
                    print(f"[=] {name} (CL {cl_int}) aggiornato (hash uguale).")
                    logf.write(f"SKIPPED: opponents/{fname}\n")
                    continue

            src_url = f"https://swse.fandom.com/wiki/{title.replace(' ', '_')}"
            tags = ["bestiario", "swse", f"cl/{cl_int}", f"type/{logical_type.lower()}"]

            fm = {
                # info sistema
                'system': 'swse',
                # identificazione
                'monster': name,          # aiuta l’indicizzazione del plugin
                'name': name,
                'bestiary': True, 
                'type': logical_type,     # header layout
                'type_line': blk['type_line'],  # dettaglio di classe/taglia
                'cl': cl_int,
                # core
                'initiative': blk['initiative'],
                'senses': blk['senses'],
                'perception': blk['perception'],
                'reflex': blk['reflex'],
                'fortitude': blk['fortitude'],
                'will': blk['will'],
                'hp': blk['hp'],
                'threshold': blk['threshold'],
                'speed': blk['speed'],
                # offense
                'melee': blk['melee'],
                'ranged': blk['ranged'],
                'attackOptions': blk['attackOptions'],
                'specialActions': blk['specialActions'],
                # features
                'specialQualities': blk['specialQualities'],
                'talents': blk['talents'],
                'feats': blk['feats'],
                'skills': blk['skills'],
                # force
                'useTheForce': blk['useTheForce'],
                'forcePowers': blk['forcePowers'],
                # gear
                'equipment': blk['equipment'],
                # abilities
                'abilities': blk['abilities'],  # stringa normalizzata
                'stats': blk['stats'],          # oggetto per tabella del layout
                # misc
                'languages': blk['languages'],
                'notes': blk['notes'],
                'source': f"SWSE Wiki – {src_url}",
                'source_book': blk['source_book'] or "",
                # meta
                'tags': tags,
                'import_hash': hash_val,
                'imported_at': iso_now_utc(),
                # Fantasy Statblocks
                'statblock': True,
                'layoutId': 'swse-creature-layout',
                'layout': "SWSE Creature"
            }

            yaml = dump_frontmatter(fm)
            body = ""  # opzionale: aggiungere fluff pulito qui
            note_content = yaml + ("\n" + body if body else "\n")

            if dry_run:
                action = "Would CREATE" if not exists else "Would UPDATE"
                print(f"{action}: {filename} (source page: {title})")
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(note_content)
                if exists:
                    print(f"[U] Aggiornato: {name} (CL {cl_int}) -> {filename}")
                    logf.write(f"UPDATED: opponents/{fname}\n")
                else:
                    print(f"[+] Creato: {name} (CL {cl_int}) -> {filename}")
                    logf.write(f"CREATED: opponents/{fname}\n")

            time.sleep(0.4)

    logf.close()

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import SWSE Opponents into Obsidian Vault")
    parser.add_argument("--entity", choices=list(ENTITY_CONFIG.keys()), required=True)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    vp = args.vault
    if not os.path.isdir(vp):
        print(f"Errore: il percorso vault '{vp}' non esiste.")
        sys.exit(1)

    import_entity(args.entity, vp, limit=args.limit, dry_run=args.dry_run, force=args.force)
