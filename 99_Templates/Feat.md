---
type: feat
name: "<% tp.file.title %>"
source_book: "<%* const sb = await tp.system.prompt('Sigla manuale origine (es: SECR)'); tR += sb ?? '' %>"
page: "<%* const pg = await tp.system.prompt('Pagina del manuale (se nota)'); tR += pg ?? '' %>"
prerequisites: []
benefit: ""
normal: ""
special: ""
tags: [SWSE, Feat]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Prerequisiti:** <% tp.file.cursor() %>  
**Beneficio:**  
**Normal:**  
**Special:**  

*Fonte:* <%* if (sb) { tR += `Manuale ${sb}`; } if (pg) { tR += `, pag. ${pg}`; } %>.

