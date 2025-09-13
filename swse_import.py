#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
swse_import.py — Importa contenuti dalla SWSE Wikia nel Vault Obsidian.

NOVITÀ: supporto completo per "Opponents" (Allies and Opponents):
- Heroic Units
- Nonheroic Units
- Beasts
- General Units
- Droids

Output:
- File Markdown in 05_Bestiario/ con naming: "CL{XX} - {Nome}.md"
- Frontmatter YAML compatibile con Fantasy Statblocks (layout "SWSE Creature")
- Campi chiave per Dataview (cl, tags con cl/XX e type/<tipo>)

Uso esempi:
    python swse_import.py --entity opponents --vault "/path/al/vault"
    python swse_import.py --entity opponents --vault "/path/al/vault" --limit 25 --force
    python swse_import.py --entity feats --vault "/path/al/vault" --limit 5

Requisiti:
    pip install requests mwparserfromhell
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
    'feats':     {'category': 'Category:Feats',          'out_dir': '03_Regole/03.05_Feat'},
    'talents':   {'category': 'Category:Talent Trees',   'out_dir': '03_Regole/03.04_Talenti'},
    'species':   {'category': 'Category:Species',        'out_dir': '03_Regole/03.02_Specie'},
    'classes':   {'category': 'Category:Heroic Classes', 'out_dir': '03_Regole/03.01_Classi'},
    'skills':    {'category': 'Category:Skills',         'out_dir': '03_Regole/03.03_Abilita'},
    'equipment': {'category': 'Category:Equipment',      'out_dir': '04_Equipaggiamento'},
    'weapons':   {'category': 'Category:Weapons',        'out_dir': '04_Equipaggiamento/04.01_Armi'},
    'armors':    {'category': 'Category:Armor',          'out_dir': '04_Equipaggiamento/04.02_Armature'},
    'vehicles':  {'category': 'Category:Vehicles',       'out_dir': '04_Equipaggiamento/04.03_Veicoli'},
    'starships': {'category': 'Category:Starships',      'out_dir': '04_Equipaggiamento/04.04_Astronavi'},
    'planets':   {'category': 'Category:Planets',        'out_dir': '06_Luoghi'},
    'prestige_classes': {'category': ['Category:Prestige Classes', 'Category:Prestige classes'], 'out_dir': '03_Regole/03.01_Classi/Prestige'},
    # NUOVO:
    'opponents': {'category': list(OPPONENT_CATEGORIES.values()), 'out_dir': '05_Bestiario'}
}

SKILL_TITLES = {
    "Acrobatics","Climb","Deception","Endurance","Gather Information",
    "Initiative","Jump","Knowledge","Mechanics","Perception","Persuasion",
    "Pilot","Ride","Stealth","Survival","Swim","Treat Injury",
    "Use Computer","Use the Force"
}

# ----------------- UTIL -----------------
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

# ----------------- WIKITEXT -> MARKDOWN (generico) -----------------
def wikitext_to_markdown(wikitext: str, link_resolver=None) -> str:
    t = wikitext
    t = re.sub(r'\[\[(?:Category|File|Image):[^\]]+\]\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'</?noinclude>', '', t, flags=re.IGNORECASE)
    t = convert_wikitable_to_md(t)

    # liste
    def repl_ul(m):
        stars, content = m.group(1), m.group(2)
        indent = '    ' * (len(stars) - 1)
        return f"{indent}- {content}".rstrip()
    t = re.sub(r'^(?P<stars>\*+)\s*(?P<content>.+)$', repl_ul, t, flags=re.MULTILINE)

    def repl_ol(m):
        hashes, content = m.group(1), m.group(2)
        indent = '    ' * (len(hashes) - 1)
        return f"{indent}1. {content}".rstrip()
    t = re.sub(r'^(?P<hashes>#+)\s*(?P<content>.+)$', repl_ol, t, flags=re.MULTILINE)

    # enfasi
    t = t.replace("'''''", "§§§")
    t = re.sub(r"'''(.*?)'''", r"**\1**", t, flags=re.DOTALL)
    t = re.sub(r"''(.*?)''",   r"*\1*",   t, flags=re.DOTALL)
    t = t.replace("§§§", "***")

    # wikilink
    def repl_wikilink(m):
        page = m.group(1).strip()
        anchor = m.group(2).strip() if m.group(2) else None
        label = m.group(3).strip() if m.group(3) else None
        if link_resolver:
            return link_resolver(page, anchor, label)
        return m.group(0)
    t = re.sub(r'\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]', repl_wikilink, t)

    # link esterni
    t = re.sub(r'\[(https?://[^\s\]]+)\s+([^\]]+)\]', r'[\2](\1)', t)

    # template
    t = re.sub(r'\{\{.*?\}\}', '', t, flags=re.DOTALL)

    # headings
    t = re.sub(r'======\s*(.*?)\s*======', r'###### \1', t)
    t = re.sub(r'=====\s*(.*?)\s*=====',   r'##### \1', t)
    t = re.sub(r'====\s*(.*?)\s*====',     r'#### \1',  t)
    t = re.sub(r'===\s*(.*?)\s*===',       r'### \1',   t)
    t = re.sub(r'==\s*(.*?)\s*==',         r'## \1',    t)
    t = re.sub(r'=\s*(.*?)\s*=',           r'# \1',     t)

    # definizioni
    t = re.sub(r'^\;\s*(.+)\n\:\s*(.+)$', r'**\1** — \2', t, flags=re.MULTILINE)

    t = t.replace('\r', '')
    t = re.sub(r'\n{3,}', '\n\n', t).strip()
    return t

# ----------------- FETCH -----------------
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

def fetch_skill_pages():
    params = {'action': 'parse', 'page': 'Skills', 'prop': 'links', 'pllimit': 'max', 'format': 'json'}
    res = api_get(params)
    titles = []
    if res and 'parse' in res and 'links' in res['parse']:
        for ln in res['parse']['links']:
            title = ln.get('*') or ln.get('title')
            if ln.get('ns') == 0 and title in SKILL_TITLES:
                titles.append(title)
    if not titles:
        titles = sorted(SKILL_TITLES)
    return titles

# ----------------- PARSER: OPPONENTS -----------------
_HDR_RE = re.compile(r'==+\s*(?P<name>[^=\n]+?)\s+Statistics\s*\(CL\s*(?P<cl>\d+)\s*\)\s*==+', re.IGNORECASE)

def _grab_first(regex, text):
    m = regex.search(text)
    return m.group(1).strip() if m else ""

def _grab_all_lines(prefix, text):
    # estrae tutte le righe che iniziano con "Prefix:"
    patt = re.compile(rf'^{prefix}\s*:\s*(.+)$', re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in patt.findall(text)]

def _split_list(s):
    if not s:
        return []
    # split su ';' preferito, fallback su ', ' preservando parentesi
    parts = re.split(r';\s*', s)
    if len(parts) == 1:
        parts = re.split(r',\s*(?=[A-Z0-9\(])', s)
    return [p.strip(' ;,') for p in parts if p.strip(' ;,')]

def parse_opponent_sections(page_title: str, wikitext: str) -> list[dict]:
    """
    Ritorna una lista di statblock estratti dalla pagina.
    Supporta più sezioni '== Name Statistics (CL X) ==' nella stessa pagina.
    """
    res = []
    # individua sezioni
    headers = [(m.start(), m.end(), m.group('name').strip(), int(m.group('cl'))) for m in _HDR_RE.finditer(wikitext)]
    if not headers:
        # fallback: prova a estrarre un singolo blocco da tutta la pagina
        # CL ovunque
        mcl = re.search(r'\bCL\s*(\d{1,2})\b', wikitext, re.IGNORECASE)
        cl = int(mcl.group(1)) if mcl else None
        block = extract_fields_from_block(page_title, cl, wikitext)
        if block:
            res.append(block)
        return res

    # per ogni sezione, prendi contenuto fino alla successiva heading
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

    # TYPE LINE: spesso prima delle statistiche c'è una riga con taglia/tipo/livelli
    # prendi la prima riga non vuota che non è heading
    type_line = ""
    for ln in t.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(('{|','!','|-','|}')):
            continue
        if re.match(r'^(?:''' + "|".join([
            'Initiative','Senses','Perception','Languages','Reflex','Fortitude','Will',
            'Hit Points','Damage Threshold','Speed','Melee','Ranged','Attack Options',
            'Special Actions','Talents','Feats','Skills','Force Power Suite','Possessions',
            'Equipment','Weapons','Abilities','Immune','Special Qualities','Species Traits'
        ]) + r')', ln, re.IGNORECASE):
            break
        # possibile riga tipo
        type_line = ln
        break

    # campi base
    name = name_guess.strip()
    cl = cl_guess if cl_guess is not None else (int(re.search(r'\bCL\s*(\d{1,2})\b', t, re.IGNORECASE).group(1))
                                                if re.search(r'\bCL\s*(\d{1,2})\b', t, re.IGNORECASE) else None)

    # difese / vitali
    initiative = _grab_first(re.compile(r"'''?Initiative:?'''?\s*([^\n]+)", re.IGNORECASE), t) or \
                 _grab_first(re.compile(r"\bInitiative\s*:\s*([^\n]+)", re.IGNORECASE), t)

    senses = _grab_first(re.compile(r"\bSenses\s*:\s*([^\n]+)", re.IGNORECASE), t)
    perception = _grab_first(re.compile(r"\bPerception\s*\+?([-\d]+)", re.IGNORECASE), t)
    if perception and not senses:
        senses = f"Perception +{perception}"

    reflex = _grab_first(re.compile(r"\bReflex(?: Defense)?\s*:\s*([^\n]+)", re.IGNORECASE), t)
    fortitude = _grab_first(re.compile(r"\bFortitude(?: Defense)?\s*:\s*([^\n]+)", re.IGNORECASE), t)
    will = _grab_first(re.compile(r"\bWill(?: Defense)?\s*:\s*([^\n]+)", re.IGNORECASE), t)

    hp = _grab_first(re.compile(r"\bHit Points?\s*:\s*([^\n]+)", re.IGNORECASE), t)
    threshold = _grab_first(re.compile(r"\bDamage Threshold\s*:\s*([^\n]+)", re.IGNORECASE), t)

    speed = _grab_first(re.compile(r"\bSpeed\s*:\s*([^\n]+)", re.IGNORECASE), t)

    # attacchi
    melee_lines = _grab_all_lines("Melee", t)
    ranged_lines = _grab_all_lines("Ranged", t)

    # opzioni e azioni
    attack_opts = _grab_first(re.compile(r"\bAttack Options\s*:\s*([^\n]+)", re.IGNORECASE), t)
    special_actions = _grab_first(re.compile(r"\bSpecial Actions\s*:\s*([^\n]+)", re.IGNORECASE), t)

    # blocchi elenco
    talents = _split_list(_grab_first(re.compile(r"'''?Talents:?'''?\s*([^\n]+)", re.IGNORECASE), t))
    feats = _split_list(_grab_first(re.compile(r"'''?Feats:?'''?\s*([^\n]+)", re.IGNORECASE), t))
    skills = _split_list(_grab_first(re.compile(r"'''?Skills:?'''?\s*([^\n]+)", re.IGNORECASE), t))
    special_qualities = _split_list(
        _grab_first(re.compile(r"(?:Special Qualities|Species Traits)\s*:\s*([^\n]+)", re.IGNORECASE), t)
    )

    # Force
    utf_bonus = _grab_first(re.compile(r"\bUse the Force\s*\+([-\d]+)", re.IGNORECASE), t)
    use_the_force = f"+{utf_bonus}" if utf_bonus else ""
    # Force Power Suite: "Force Power Suite (Use the Force +X): A, B, C"
    fps_line = _grab_first(re.compile(r"Force Power Suite[^\n]*:\s*([^\n]+)", re.IGNORECASE), t)
    force_powers = _split_list(re.sub(r'^\([^)]*\)\s*', '', fps_line)) if fps_line else []

    # Equipaggiamento / Possessi
    eq_line = (_grab_first(re.compile(r"(?:Possessions|Equipment|Weapons)\s*:\s*([^\n]+)", re.IGNORECASE), t))
    equipment = _split_list(eq_line)

    # Abilities
    abil = _grab_first(re.compile(r"\bAbilities\s*:\s*([^\n]+)", re.IGNORECASE), t)
    abilities = ""
    if abil:
        # normalizza in formato "Str 12; Dex 14; Con 10; Int 13; Wis 12; Cha 11"
        s = abil
        s = s.replace(',', ';')
        s = re.sub(r'\s*;\s*', '; ', s)
        abilities = s

    # Languages
    languages = _grab_first(re.compile(r"\bLanguages\s*:\s*([^\n]+)", re.IGNORECASE), t)

    # Note: cattura righe con asterisco o trattini lunghi
    notes = []
    for ln in t.splitlines():
        if ln.strip().startswith('*') or '—' in ln:
            clean = mwparserfromhell.parse(ln.strip()).strip_code().strip()
            if clean and not re.match(r"^\*+\s*(?:See|Source|Reference)", clean, re.IGNORECASE):
                notes.append(clean)
    notes = " ".join(notes) if notes else ""

    # Source
    m_source = re.search(r"Reference Book\s*:\s*([^\n(]+)", t, re.IGNORECASE)
    source_book = m_source.group(1).strip() if m_source else ""
    source = source_book if source_book else "SWSE Wiki"

    # Se manca il nome, usa name_guess
    name = name_guess or "Unknown"

    return {
        'name': name,
        'type_line': type_line,
        'cl': cl if cl is not None else "",
        'initiative': initiative,
        'senses': senses,
        'perception': f"+{perception}" if perception and not senses else "",
        'reflex': reflex,
        'fortitude': fortitude,
        'will': will,
        'hp': hp,
        'threshold': threshold,
        'speed': speed,
        'melee': melee_lines,
        'ranged': ranged_lines,
        'attackOptions': attack_opts,
        'specialActions': special_actions,
        'specialQualities': special_qualities,
        'talents': talents,
        'feats': feats,
        'skills': skills,
        'useTheForce': use_the_force,
        'forcePowers': force_powers,
        'equipment': equipment,
        'abilities': abilities,
        'languages': languages,
        'notes': notes,
        'source_book': source
    }

# ----------------- YAML / WRITE -----------------
def dump_frontmatter(frontmatter: dict) -> str:
    def dump_val(v, indent=0):
        if isinstance(v, list):
            if not v:
                return "[]"
            # inline list per semplicità
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
    s = str(v)
    if s == "" or any(ch in s for ch in [":", "-", "[", "]", "{", "}", "#", ",", '"', "'"]):
        s = s.replace('"', '\\"')
        return f"\"{s}\""
    return s

def convert_wikitable_to_md(t: str) -> str:
    def strip_cell_attrs(cell: str) -> str:
        s = cell.strip()
        if s.startswith("[["):
            return s
        return re.sub(r'^[^|]*\|\s*', '', s)

    def parse_table(m):
        block = m.group(1)
        lines = [ln.strip() for ln in block.splitlines()
                 if ln.strip() and not ln.strip().startswith('|+')]
        header, rows, cur = [], [], []

        def flush_row():
            nonlocal cur, rows
            if cur:
                rows.append(cur)
                cur = []

        for s in lines:
            if s.startswith('|-'):
                flush_row(); continue
            if s.startswith('!'):
                cells = [strip_cell_attrs(c) for c in re.split(r'\s*!!\s*', s.lstrip('!').strip())]
                header.extend(cells); continue
            if s.startswith('|'):
                cells = [strip_cell_attrs(c) for c in re.split(r'\s*\|\|\s*', s.lstrip('|').strip())]
                cur.extend(cells); continue
        flush_row()

        if not header and rows:
            header = [''] * len(rows[0])
        if not header:
            return ""

        rows = [r + [''] * (len(header) - len(r)) for r in rows]

        md = "| " + " | ".join(header) + " |\n"
        md += "| " + " | ".join(["---"] * len(header)) + " |\n"
        for r in rows:
            md += "| " + " | ".join(r) + " |\n"
        return "\n\n" + md + "\n\n"

    return re.sub(r'\{\|[^\n]*\n(.*?)\n\|\}', parse_table, t, flags=re.DOTALL)

# ----------------- IMPORT CORE -----------------
def import_entity(entity, vault_path, limit=0, dry_run=False, force=False):
    if entity not in ENTITY_CONFIG:
        print(f"Entità '{entity}' non supportata.")
        return

    cfg = ENTITY_CONFIG[entity]
    out_dir = os.path.join(vault_path, cfg['out_dir'])
    os.makedirs(out_dir, exist_ok=True)

    # log
    log_file = os.path.join(vault_path, "98_Imports_SWSE", "import.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logf = open(log_file, "a", encoding="utf-8")

    slug_index = build_slug_index(vault_path)
    link_resolver = make_link_resolver(vault_path, slug_index)

    # selezione pagine
    if entity == 'skills':
        titles = fetch_skill_pages()
        members = [{'title': t, 'pageid': None} for t in titles]
    elif entity == 'opponents':
        members = []
        for tlabel, cat in OPPONENT_CATEGORIES.items():
            ms = fetch_category_members(cat, limit=0 if not limit else max(1, limit - len(members)))
            for m in ms:
                m = dict(m)
                m['__unit_kind'] = tlabel  # Heroic / Nonheroic / Beast / General / Droid
                members.append(m)
            if limit and len(members) >= limit:
                members = members[:limit]
                break
        # deduplica su pageid mantenendo la priorità dei kind: Heroic > Nonheroic > Beast > Droid > General
        priority = {"Heroic":5, "Nonheroic":4, "Beast":3, "Droid":2, "General":1}
        dedup = {}
        for m in members:
            pid = m.get('pageid')
            if pid not in dedup or priority[m['__unit_kind']] > priority[dedup[pid]['__unit_kind']]:
                dedup[pid] = m
        members = list(dedup.values())
    else:
        members = fetch_category_members(cfg['category'], limit=limit)

    if not members:
        print(f"Nessun risultato in {cfg['category']}")
        return
    print(f"Trovate {len(members)} pagine per '{entity}'.")

    count = 0
    for mem in members:
        title = mem['title']
        pageid = mem.get('pageid')
        unit_kind_hint = mem.get('__unit_kind')  # solo per opponents
        count += 1
        if limit and count > limit:
            break

        # fetch contenuto wikitext
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

        if entity != 'opponents':
            # fallback generico identico a versione precedente (conversione wikitext)
            hash_val = hashlib.sha256(wikitext.encode('utf-8')).hexdigest()
            slug = title_to_slug(title)
            filename = os.path.join(out_dir, f"{slug}.md")
            exists = os.path.isfile(filename)
            if exists and not force:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                m = re.search(r"import_hash:\s*([0-9a-fA-F]+)", content)
                old_hash = m.group(1) if m else ""
                if old_hash == hash_val:
                    print(f"[=] {title} aggiornato (hash uguale).")
                    logf.write(f"SKIPPED: {entity}/{slug}.md\n")
                    continue

            frontmatter = {
                'name': title,
                'type': 'feat' if entity == 'feats' else entity.rstrip('s'),
                'slug': slug,
                'source_url': f"https://swse.fandom.com/wiki/{title.replace(' ', '_')}",
                'source_license': "CC BY-SA 3.0 (Fandom)",
                'import_hash': hash_val,
                'last_imported': datetime.now().strftime("%Y-%m-%d"),
                'tags': ['SWSE', entity[:-1].capitalize() if entity.endswith('s') else entity.capitalize()]
            }
            body_md = wikitext_to_markdown(wikitext, link_resolver)
            yaml = dump_frontmatter(frontmatter)
            note_content = yaml + "\n" + body_md

            if dry_run:
                action = "Would CREATE" if not exists else "Would UPDATE"
                print(f"{action}: {filename} (source: {title})")
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(note_content)
                if exists:
                    print(f"[U] Aggiornato: {title} -> {filename}")
                    logf.write(f"UPDATED: {entity}/{slug}.md\n")
                else:
                    print(f"[+] Creato: {title} -> {filename}")
                    logf.write(f"CREATED: {entity}/{slug}.md\n")
            # aggiorna indice
            rel = os.path.relpath(filename, os.path.abspath(vault_path)).replace("\\", "/")
            slug_index[slug] = rel
            time.sleep(0.5)
            continue

        # entity == opponents
        # parse possibili più sezioni
        blocks = parse_opponent_sections(title, wikitext)
        if not blocks:
            print(f"WARN: nessun statblock trovato in '{title}'.")
            logf.write(f"WARN: no statblock {title}\n")
            continue

        for blk in blocks:
            name = blk['name']
            cl = blk['cl'] if isinstance(blk['cl'], int) or str(blk['cl']).isdigit() else 0
            cl_int = int(cl) if str(cl).isdigit() else 0

            # tipo logico (Heroic/Nonheroic/Beast/General/Droid)
            logical_type = infer_unit_kind(unit_kind_hint, blk)

            # costruiamo frontmatter per Fantasy Statblocks + Dataview
            # hash calcolato sul payload dati essenziali
            payload = {
                k: blk[k] for k in [
                    'name','type_line','cl','initiative','senses','perception','reflex','fortitude','will',
                    'hp','threshold','speed','melee','ranged','attackOptions','specialActions',
                    'specialQualities','talents','feats','skills','useTheForce','forcePowers',
                    'equipment','abilities','languages','notes','source_book'
                ]
            }
            hash_val = hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

            # filename "CL{XX} - {Nome}.md"
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

            # URL sorgente
            src_url = f"https://swse.fandom.com/wiki/{title.replace(' ', '_')}"

            # TAGS
            tags = [
                "bestiario", "swse",
                f"cl/{cl_int}",
                f"type/{logical_type.lower()}"
            ]

            # FRONTMATTER conforme specifica + campi layout
            fm = {
                'system': 'swse',
                'name': name,
                'type': logical_type,
                'type_line': blk['type_line'],
                'cl': cl_int,
                'initiative': blk['initiative'],
                'senses': blk['senses'],
                'perception': blk['perception'],
                'reflex': blk['reflex'],
                'fortitude': blk['fortitude'],
                'will': blk['will'],
                'hp': blk['hp'],
                'threshold': blk['threshold'],
                'speed': blk['speed'],
                'melee': blk['melee'],
                'ranged': blk['ranged'],
                'attackOptions': blk['attackOptions'],
                'specialActions': blk['specialActions'],
                'specialQualities': blk['specialQualities'],
                'talents': blk['talents'],
                'feats': blk['feats'],
                'skills': blk['skills'],
                'useTheForce': blk['useTheForce'],
                'forcePowers': blk['forcePowers'],
                'equipment': blk['equipment'],
                'abilities': blk['abilities'],
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
                'layout': "SWSE Creature"
            }

            yaml = dump_frontmatter(fm)
            body = ""  # opzionale: descrizione/fluff; per ora vuoto

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

            # aggiorna indice per i link successivi
            rel = os.path.relpath(filename, os.path.abspath(vault_path)).replace("\\", "/")
            slug_index[os.path.splitext(os.path.basename(filename))[0]] = rel

            time.sleep(0.4)

    logf.close()

def infer_unit_kind(kind_hint: str | None, blk: dict) -> str:
    """
    Determina il tipo logico per i tag e per 'type' nel frontmatter:
    'Heroic' | 'Nonheroic' | 'Beast' | 'General' | 'Droid'
    """
    if kind_hint in {"Heroic","Nonheroic","Beast","General","Droid"}:
        return kind_hint
    tl = (blk.get('type_line') or "").lower()
    name = (blk.get('name') or "").lower()
    # regole euristiche
    if "droid" in tl or "droid" in name:
        return "Droid"
    if "beast" in tl:
        return "Beast"
    if "nonheroic" in tl:
        return "Nonheroic"
    if any(k in tl for k in ["soldier","scout","noble","scoundrel","jedi","ace pilot","bounty hunter"]):
        return "Heroic"
    return "General"

# ----------------- IMPORT ALL -----------------
def import_all(vault_path, limit=0, dry_run=False, force=False):
    for ent in ENTITY_CONFIG.keys():
        import_entity(ent, vault_path, limit=limit, dry_run=dry_run, force=force)

# ----------------- CLI -----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import SWSE Wiki content into Obsidian Vault")
    parser.add_argument("--entity", choices=list(ENTITY_CONFIG.keys())+["all"], required=True)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    vp = args.vault
    if not os.path.isdir(vp):
        print(f"Errore: il percorso vault '{vp}' non esiste.")
        sys.exit(1)

    if args.entity == "all":
        import_all(vp, limit=args.limit, dry_run=args.dry_run, force=args.force)
    else:
        import_entity(args.entity, vp, limit=args.limit, dry_run=args.dry_run, force=args.force)
