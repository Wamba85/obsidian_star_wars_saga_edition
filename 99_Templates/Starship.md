---
type: starship
name: "<% tp.file.title %>"
starship_type: "<%* let stype = await tp.system.prompt('Tipo (Starfighter/Transport/Capital)'); tR += stype %>"
size: "Colossal"
occupants: ""
init: ""
maneuver: ""
speed_space: ""
speed_atmosphere: ""
defenses: ""
hp: ""
shields: ""
damage_threshold: ""
armor: ""
hyperdrive: ""
weapons: []
special: ""
source_book: "<%* let sb = await tp.system.prompt('Manuale'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Starship]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Equipaggio/Passeggeri:** <% tp.file.cursor() %>  
**Iniziativa:**    **ManovrabilitÃ :**   
**VelocitÃ  (spazio):**    **(atmosfera):**   
**Difese:**   
**PF:**    **Scudi:**    **Soglia Danni:**   
**Armatura (DR):**    **Iperguida:**   

**Armamenti:**  
- <!-- Armi di bordo -->

**Sistemi / Note:**  
<!-- Es. sensori, capsule di salvataggio, hangar, etc. -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

