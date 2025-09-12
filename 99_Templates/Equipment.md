---
type: equipment
name: "<% tp.file.title %>"
category: "<%* let cat = await tp.system.prompt('Categoria (es: Medical, Tool)'); tR += cat %>"
cost: ""
weight: ""
availability: ""
description: ""
source_book: "<%* let sb = await tp.system.prompt('Manuale'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Equipment]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Costo:** <% tp.file.cursor() %>  
**Peso:**   
**DisponibilitÃ :** <%* if (cat) { tR += `{{cat}}`; } %>  

**Descrizione:**  
<!-- Descrizione dell'oggetto e utilizzo in gioco -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

