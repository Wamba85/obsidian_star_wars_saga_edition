#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
swse_import.py - Importa contenuti dalla Star Wars Saga Edition Wikia nel Vault Obsidian.

Uso:
    python swse_import.py --entity feats --vault "." --limit 5
    python swse_import.py --entity talents --vault "." --limit 5 --force

Parametri:
    --entity  feats, talents, species, classes, skills, equipment, weapons, armors, vehicles, starships, planets, all
    --vault   Percorso del Vault Obsidian
    --limit   Limite risultati (0 = max)
    --dry-run Non scrive file
    --force   Ignora hash ed esegue update
"""
import os
import re
import sys
import time
import hashlib
import argparse
import requests

try:
    import mwparserfromhell
except ImportError:
    sys.stderr.write("Errore: manca mwparserfromhell. Esegui: pip install mwparserfromhell requests\n")
    sys.exit(1)

API_URL = "https://swse.fandom.com/api.php"

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
}

SKILL_TITLES = {
    "Acrobatics","Climb","Deception","Endurance","Gather Information",
    "Initiative","Jump","Knowledge","Mechanics","Perception","Persuasion",
    "Pilot","Ride","Stealth","Survival","Swim","Treat Injury",
    "Use Computer","Use the Force"
}

# --------- UTIL ---------
def title_to_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    return slug

def api_get(params):
    retries = 3
    for i in range(retries):
        try:
            r = requests.get(API_URL, params=params, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            sys.stderr.write(f"API error {i+1}/{retries}: {e}\n")
        time.sleep(1 + i)
    return None

def build_slug_index(vault_path: str) -> dict:
    """Indicizza tutte le note .md del vault: slug (nome file senza estensione) -> percorso relativo"""
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
    """Ritorna funzione che converte [[Pagina|Label]] wiki in link Obsidian se possibile, altrimenti link esterno."""
    vp = os.path.abspath(vault_path)
    def resolver(page_title: str, anchor: str | None, label: str | None) -> str:
        if page_title.startswith(("Category:", "File:", "Image:", "Template:")):
            return ""  # rimuovi categorie/file/template
        page_title = page_title.strip()
        alias = (label or page_title).strip()
        slug = title_to_slug(page_title)
        # link interno se esiste una nota con quel slug
        if slug in slug_index:
            target = slug_index[slug]
            if anchor:
                target = f"{target}#{anchor}"
            return f"[[{target}|{alias}]]"
        # fallback a link esterno fandom
        url = f"https://swse.fandom.com/wiki/{page_title.replace(' ', '_')}"
        if anchor:
            url += f"#{anchor.replace(' ', '_')}"
        return f"[{alias}]({url})"
    return resolver

# --------- WIKITEXT -> MARKDOWN ---------
def wikitext_to_markdown(wikitext: str, link_resolver=None) -> str:
    t = wikitext

    # 0) Rimuovi categorie e file/link media a monte
    t = re.sub(r'\[\[(?:Category|File|Image):[^\]]+\]\]', '', t, flags=re.IGNORECASE)

    t = re.sub(r'</?noinclude>', '', t, flags=re.IGNORECASE)

    t = convert_wikitable_to_md(t)

    # 1) LISTE prima dei titoli (= ... =), così non confondiamo i # dei titoli Markdown
    #   * → - con indentazione
    def repl_ul(m):
        stars = m.group(1)
        content = m.group(2)
        indent = '    ' * (len(stars) - 1)
        return f"{indent}- {content}".rstrip()
    t = re.sub(r'^(?P<stars>\*+)\s*(?P<content>.+)$', repl_ul, t, flags=re.MULTILINE)

    #   # → 1. con indentazione
    def repl_ol(m):
        hashes = m.group(1)
        content = m.group(2)
        indent = '    ' * (len(hashes) - 1)
        return f"{indent}1. {content}".rstrip()
    t = re.sub(r'^(?P<hashes>#+)\s*(?P<content>.+)$', repl_ol, t, flags=re.MULTILINE)

    # 2) Grassetto/Corsivo
    t = t.replace("'''''", "§§§")  # salva bold+italic
    t = re.sub(r"'''(.*?)'''", r"**\1**", t, flags=re.DOTALL)
    t = re.sub(r"''(.*?)''",   r"*\1*",   t, flags=re.DOTALL)
    t = t.replace("§§§", "***")

    # 3) Link interni [[Page|Label]] con resolver verso note locali quando esistono
    def repl_wikilink(m):
        page = m.group(1).strip()
        anchor = m.group(2).strip() if m.group(2) else None
        label = m.group(3).strip() if m.group(3) else None
        if link_resolver:
            return link_resolver(page, anchor, label)
        # fallback: lascia wikilink inalterato
        return m.group(0)
    t = re.sub(r'\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]', repl_wikilink, t)

    # 4) Link esterni [url label] → [label](url)
    t = re.sub(r'\[(https?://[^\s\]]+)\s+([^\]]+)\]', r'[\2](\1)', t)

    # 5) Template {{...}} → rimuovi
    t = re.sub(r'\{\{.*?\}\}', '', t, flags=re.DOTALL)

    # 6) Headings (= … =) → Markdown
    t = re.sub(r'======\s*(.*?)\s*======', r'###### \1', t)
    t = re.sub(r'=====\s*(.*?)\s*=====', r'##### \1', t)
    t = re.sub(r'====\s*(.*?)\s*====',   r'#### \1',  t)
    t = re.sub(r'===\s*(.*?)\s*===',     r'### \1',   t)
    t = re.sub(r'==\s*(.*?)\s*==',       r'## \1',    t)
    t = re.sub(r'=\s*(.*?)\s*=',         r'# \1',     t)

    # 7) Definizioni ;term \n :def → **term** — def
    t = re.sub(r'^\;\s*(.+)\n\:\s*(.+)$', r'**\1** — \2', t, flags=re.MULTILINE)

    # 8) Pulizia
    t = t.replace('\r', '')
    t = re.sub(r'\n{3,}', '\n\n', t).strip()
    return t

# --------- PARSER ENTITÀ ---------
def parse_feat_content(wikitext: str, link_resolver=None) -> dict:
    feat = {}
    patterns = {
        'prerequisites': re.compile(r"'''?Prerequisites:?'''?\s*(.+)"),
        'benefit':       re.compile(r"'''?Benefit:?'''?\s*(.+)"),
        'effect':        re.compile(r"'''?Effect:?'''?\s*(.+)"),
        'normal':        re.compile(r"'''?Normal:?'''?\s*(.+)"),
        'special':       re.compile(r"'''?Special:?'''?\s*(.+)")
    }
    lines = wikitext.splitlines()
    for i, line in enumerate(lines):
        for key, regex in patterns.items():
            m = regex.match(line)
            if m:
                content = m.group(1).strip()
                j = i + 1
                while j < len(lines) and not re.match(r"^'''[A-Z]", lines[j]):  # fino al prossimo campo bold
                    content += " " + lines[j].strip()
                    j += 1
                if key == 'effect':
                    feat['benefit'] = wikitext_to_markdown(content, link_resolver)
                else:
                    feat[key] = wikitext_to_markdown(content, link_resolver)

    m = re.search(r"Reference Book:\s*([^(\n]+)", wikitext)
    if m:
        source_full = m.group(1).strip()
        abbr = {
            "Star Wars Saga Edition Core Rulebook": "SECR",
            "Star Wars Saga Edition": "SECR",
            "Knights of the Old Republic Campaign Guide": "KOTORCG",
            "The Force Unleashed Campaign Guide": "FUCG",
            "Galaxy at War": "GaW",
            "Galaxy of Intrigue": "GoI",
            "Threats of the Galaxy": "TotG",
            "Unknown Regions": "UR",
        }
        feat['source_book'] = next((s for f, s in abbr.items() if source_full.startswith(f)), source_full)

    for field in ['prerequisites', 'benefit', 'normal', 'special']:
        feat.setdefault(field, "")
    return feat

def parse_prestige_class_content(wikitext: str, link_resolver=None) -> dict:
    """Estrae campi base dalle prestige class."""
    pc = {}

    # supporta sia '''Requirements:''' che == Requirements ==
    def grab_section(name):
        # forma bold+due punti
        m = re.search(rf"'''{name}s?:?'''[ \t]*([\s\S]*?)(?=\n'''[A-Z][^'\n]*'''|\n==|\Z)", wikitext, flags=re.IGNORECASE)
        if m:
            return wikitext_to_markdown(m.group(1).strip(), link_resolver)
        # forma heading
        m = re.search(rf"\n==+\s*{name}s?\s*==+\s*\n([\s\S]*?)(?=\n==|\Z)", wikitext, flags=re.IGNORECASE)
        if m:
            return wikitext_to_markdown(m.group(1).strip(), link_resolver)
        return ""

    pc['requirements']     = grab_section("Requirement")
    pc['class_skills']     = grab_section("Class Skill")
    pc['starting_feats']   = grab_section("Starting Feat")
    pc['class_features']   = grab_section("Class Feature")
    pc['hit_points']       = grab_section("Hit Point")
    pc['defense_bonuses']  = grab_section("Defense Bonus")
    pc['base_attack']      = grab_section("Base Attack")

    # source book
    m = re.search(r"Reference Book:\s*([^\n(]+)", wikitext)
    if m:
        source_full = m.group(1).strip()
        abbr = {
            "Star Wars Saga Edition Core Rulebook": "SECR",
            "Star Wars Saga Edition": "SECR",
            "Knights of the Old Republic Campaign Guide": "KOTORCG",
            "The Force Unleashed Campaign Guide": "FUCG",
            "Galaxy at War": "GaW",
            "Galaxy of Intrigue": "GoI",
            "Threats of the Galaxy": "TotG",
            "Unknown Regions": "UR",
            "Scum and Villainy": "SaV",
        }
        pc['source_book'] = next((s for f, s in abbr.items() if source_full.startswith(f)), source_full)

    return pc

def fetch_category_members(cats, limit=0):
    """Ritorna TUTTI i membri delle categorie usando cmcontinue."""
    cats = cats if isinstance(cats, list) else [cats]
    members, seen = [], set()
    for cat in cats:
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': cat,
            'cmlimit': 'max',   # 500 per utente, 5000 per bot
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
    params = {
        'action': 'parse', 'page': 'Skills', 'prop': 'links',
        'pllimit': 'max', 'format': 'json'
    }
    res = api_get(params)
    titles = []
    if res and 'parse' in res and 'links' in res['parse']:
        for ln in res['parse']['links']:
            # ns==0 = main namespace
            title = ln.get('*') or ln.get('title')
            if ln.get('ns') == 0 and title in SKILL_TITLES:
                titles.append(title)
    # fallback se la parse fallisce
    if not titles:
        titles = sorted(SKILL_TITLES)
    return titles

# --------- IMPORT ---------
def import_entity(entity, vault_path, limit=0, dry_run=False, force=False):
    if entity not in ENTITY_CONFIG:
        print(f"Entità '{entity}' non supportata.")
        return

    cfg = ENTITY_CONFIG[entity]
    cat = cfg['category']
    out_dir = os.path.join(vault_path, cfg['out_dir'])
    os.makedirs(out_dir, exist_ok=True)

    #lista pagine
    cats = cfg['category']
    if entity == 'skills':
        titles = fetch_skill_pages()
        members = [{'title': t, 'pageid': None} for t in titles]
    else:
        cats = cfg['category']
        members = fetch_category_members(cats, limit=limit)
    if not members:
        print(f"Nessun risultato in {cats}")
        return
    print(f"Trovate {len(members)} pagine in {cats}.")

    # log
    log_file = os.path.join(vault_path, "98_Imports_SWSE", "import.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logf = open(log_file, "a", encoding="utf-8")

    # indice note esistenti
    slug_index = build_slug_index(vault_path)
    link_resolver = make_link_resolver(vault_path, slug_index)

    count = 0
    for mem in members:
        title = mem['title']
        pageid = mem['pageid']
        count += 1
        if limit and count > limit:
            break

        slug = title_to_slug(title)
        filename = os.path.join(out_dir, f"{slug}.md")

        # fetch contenuto
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

        # hash sorgente
        hash_val = hashlib.sha256(wikitext.encode('utf-8')).hexdigest()

        exists = os.path.isfile(filename)
        if exists and not force:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.search(r"import_hash:\s*([0-9a-f]+)", content)
            old_hash = m.group(1) if m else ""
            if old_hash == hash_val:
                print(f"[=] {title} aggiornato (hash uguale).")
                logf.write(f"SKIPPED: {entity}/{slug}.md\n")
                continue

        # frontmatter + corpo
        frontmatter = {
            'name': title,
            'type': 'feat' if entity == 'feats' else entity.rstrip('s'),
            'slug': slug,
            'source_url': f"https://swse.fandom.com/wiki/{title.replace(' ', '_')}",
            'source_license': "CC BY-SA 3.0 (Fandom)",
            'import_hash': hash_val,
            'last_imported': time.strftime("%Y-%m-%d"),
            'tags': ['SWSE', entity[:-1].capitalize() if entity.endswith('s') else entity.capitalize()]
        }

        if entity == 'feats':
            data_fields = parse_feat_content(wikitext, link_resolver)
            frontmatter.update({k: v for k, v in data_fields.items() if v})
            # corpo leggibile con i campi principali
            parts = []
            if frontmatter.get('prerequisites'):
                parts.append(f"**Prerequisiti:** {frontmatter['prerequisites']}")
            if frontmatter.get('benefit'):
                parts.append(f"**Beneficio:** {frontmatter['benefit']}")
            if frontmatter.get('normal'):
                parts.append(f"**Normal:** {frontmatter['normal']}")
            if frontmatter.get('special'):
                parts.append(f"**Special:** {frontmatter['special']}")
            parts.append(f"*Fonte:* {frontmatter.get('source_book','')}.")
            body_md = "\n\n".join([p for p in parts if p])
        elif entity == 'prestige_classes':
            data_fields = parse_prestige_class_content(wikitext, link_resolver)
            frontmatter.update(data_fields)
            frontmatter['type'] = 'class'
            frontmatter['class_type'] = 'prestige'
            frontmatter['tags'] = ['SWSE', 'Class', 'Prestige']
            body_md = wikitext_to_markdown(wikitext, link_resolver)
        else:
            # conversione completa mantenendo bold/italic/liste/link
            body_md = wikitext_to_markdown(wikitext, link_resolver)
            frontmatter['type'] = 'skill' if entity == 'skills' else entity.rstrip('s')

        # YAML
        yaml = dump_frontmatter(frontmatter)
        note_content = yaml + "\n" + body_md

        # scrittura
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
            # aggiorna indice per risolvere link dei file successivi
            rel = os.path.relpath(filename, os.path.abspath(vault_path)).replace("\\", "/")
            slug_index[slug] = rel

        time.sleep(0.5)
    logf.close()

def convert_wikitable_to_md(t: str) -> str:
    def strip_cell_attrs(cell: str) -> str:
        s = cell.strip()
        if s.startswith("[["):  # non toccare wikilink
            return s
        return re.sub(r'^[^|]*\|\s*', '', s)  # rimuovi scope=".."|, style=..| ecc.

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

def dump_frontmatter(frontmatter: dict) -> str:
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            s = str(v)
            if "\n" in s:
                lines.append(f"{k}: |")
                for ln in s.splitlines():
                    lines.append(f"  {ln}")
            else:
                s = s.replace('"', '\\"')
                lines.append(f'{k}: "{s}"')
    lines.append("---")
    return "\n".join(lines)

def import_all(vault_path, limit=0, dry_run=False, force=False):
    for ent in ENTITY_CONFIG.keys():
        import_entity(ent, vault_path, limit=limit, dry_run=dry_run, force=force)

# --------- CLI ---------
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
