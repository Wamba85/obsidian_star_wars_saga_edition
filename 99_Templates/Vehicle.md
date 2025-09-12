---
type: vehicle
name: "<% tp.file.title %>"
vehicle_type: "<%* let vtype = await tp.system.prompt('Tipo (Speeder/Walker/etc.)'); tR += vtype %>"
size: ""
occupants: ""
init: ""
maneuver: ""
speed: ""
defenses: ""
hp: ""
damage_threshold: ""
armor: ""
weapons: []
special: ""
source_book: "<%* let sb = await tp.system.prompt('Manuale'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Vehicle]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Equipaggio/Passeggeri:** <% tp.file.cursor() %>  
**Iniziativa:**   
**ManovrabilitÃ :**   
**VelocitÃ :**   
**Difese:**   
**PF:**    **Soglia Danni:**   
**Armatura (DR):**   

**Armamenti:**  
- <!-- Elenco armi montate, es. "Cannone Laser doppio +2 (6d10)" -->

**Note speciali:**  
<!-- Altre caratteristiche: copertura fornita, sensori, ecc. -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

