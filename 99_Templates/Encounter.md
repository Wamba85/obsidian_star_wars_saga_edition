---
type: encounter
name: "<% tp.file.title %>"
challenge_level: "<%* let cl = await tp.system.prompt('CL Totale incontro'); tR += cl %>"
environment: "<%* let env = await tp.system.prompt('Ambiente (es: Urbano, Deserto)'); tR += env %>"
participants: []
reward_xp: ""
treasure: ""
notes: ""
tags: [SWSE, Encounter]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
---

**CL Incontro:** <%* if (cl) { tR += `{{cl}}`; } %> â€“ **Ambiente:** <%* if (env) { tR += `{{env}}`; } %>  
**Partecipanti:** <% tp.file.cursor() %>  
**Ricompensa XP:**   
**Tesoro/Bottino:**   

**Dettagli e Note:**  
<!-- Descrizione dell'incontro, condizioni speciali, timer, obiettivi, ecc. -->

