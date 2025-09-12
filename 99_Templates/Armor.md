---
type: armor
name: "<% tp.file.title %>"
armor_type: "<%* let atype = await tp.system.suggester(['Light','Medium','Heavy','Shield'], ['Light','Medium','Heavy','Shield']); tR += atype %>"
bonus: ""
max_dex: ""
armor_check_penalty: ""
speed: ""
weight: ""
cost: ""
availability: ""
special: ""
source_book: "<%* let sb = await tp.system.prompt('Manuale'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Armor]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Bonus Armatura:** <% tp.file.cursor() %>  
**Max Des:**   
**PenalitÃ  Armatura:**   
**VelocitÃ :** <%* if (speed) { tR += `{{speed}} quadretti`; } %>  
**Special:** <%* if (special) { tR += `{{special}}`; } %>  

*Costo:* {{cost}} cr â€“ *Peso:* {{weight}} kg â€“ *Disp:* <%* if (availability) { tR += `{{availability}}`; } %>  
*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

