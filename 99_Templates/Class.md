---
type: class
name: "<% tp.file.title %>"
class_type: "<%* let ctype = await tp.system.suggester(['Heroic','Prestige','Non-heroic'], ['Heroic','Prestige','Non-heroic']); tR += ctype %>"
hit_dice: ""
base_attack_progression: ""
defense_bonuses: ""
talents_available: []
force_points: ""
features: []
source_book: "<%* let sb = await tp.system.prompt('Manuale (es: SECR)'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Class]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Tipo:** <%* if (ctype) { tR += `{{ctype}}`; } %>  
**DV:** <% tp.file.cursor() %>  
**BAB:**   
**Difese base:**   
**Talenti:**   
**Punti Forza/liv:**   
**Privilegi di classe:**  

<small>*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += ` p.{{pg}}`; } %></small>

