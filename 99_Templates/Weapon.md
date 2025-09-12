---
type: weapon
name: "<% tp.file.title %>"
weapon_type: "<%* let wtype = await tp.system.prompt('Tipo (es: Ranged (Pistol), Melee (Simple))'); tR += wtype %>"
category: "<%* let cat = await tp.system.prompt('Categoria (es: Pistol, Rifle, Lightsaber)'); tR += cat %>"
damage: ""
stun_damage: ""
rate_of_fire: ""
range: ""
accuracy: ""
special: ""
size: ""
weight: ""
cost: ""
availability: ""
source_book: "<%* let sb = await tp.system.prompt('Manuale'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Weapon]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Danno:** <% tp.file.cursor() %>  
**Danno Stordente:**   
**ROF:**   
**Portata:**   
**Taglia arma:** <%* if (size) { tR += `{{size}}`; } %>  
**Special:** <%* if (special) { tR += `{{special}}`; } %>  

*Costo:* {{cost}} cr â€“ *Peso:* {{weight}} kg â€“ *DisponibilitÃ :* <%* if (availability) { tR += `{{availability}}`; } %>

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

