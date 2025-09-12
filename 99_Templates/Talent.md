---
type: talent
name: "<% tp.file.title %>"
talent_tree: "<%* let tree = await tp.system.prompt('Albero di talenti (es: Commando)'); tR += tree %>"
classes: []
prerequisites: []
effect: ""
special: ""
source_book: "<%* let sb = await tp.system.prompt('Sigla manuale origine'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina manuale'); tR += pg %>"
tags: [SWSE, Talent]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Prerequisiti:** <% tp.file.cursor() %>  
**Effetto:** <!-- Descrizione del talento -->  
**Special:** <!-- Note speciali, se presenti -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, pag. {{pg}}`; } %> â€“ Albero: <%* if (tree) { tR += `{{tree}}`; } %>.

