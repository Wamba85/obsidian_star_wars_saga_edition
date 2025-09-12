---
type: npc
name: "<% tp.file.title %>"
species: "<%* let sp = await tp.system.prompt('Specie'); tR += sp %>"
classes: "<%* let cls = await tp.system.prompt('Classi e livelli (es: Soldier 3/Jedi 1)'); tR += cls %>"
level: "<%* let cl = await tp.system.prompt('Challenge Level'); tR += cl %>"
role: "<%* let role = await tp.system.prompt('Ruolo (es. Mercenario, Sith Apprentice)'); tR += role %>"
affiliation: ""
tags: [SWSE, NPC]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
---

```statblock
monster: <% tp.file.title %>
sprite: skull ; <-- iconcina se supportata, qui ad esempio un teschio (opzionale) -->
property: |
  **CL**: <%* if (cl) { tR += `{{cl}}`; } %>
  **Species**: <%* if (sp) { tR += `{{sp}}`; } %>
  **Classi**: <%* if (cls) { tR += `{{cls}}`; } %>
stat: |
  **Forza** | **Destrezza** | **Costituzione** | **Intelligenza** | **Saggezza** | **Carisma**  
  10 (+0) | 10 (+0) | 10 (+0) | 10 (+0) | 10 (+0) | 10 (+0)
  **Reflex** | **Fort** | **Will** | **PF** | **Soglia**  
  10 | 10 | 10 | 0 | 0
  **Bab** | **Attacco in mischia** | **Attacco a distanza** | **Iniziativa** | **Percezione**  
  +0 | +0 | +0 | +0 | +0
action: |
  **Attacchi:**<br>
  - <!-- es. Spada laser +5 (2d8+3) --><br>
  - <!-- es. Blaster a ripetizione +2 (3d8+1) -->
trait: |
  **Talenti:** <!-- Elenco talenti -->  
  **Talent Tree:** <!-- se utile, albero talenti -->  
  **Feat:** <!-- Elenco feat -->  
  **AbilitÃ :** <!-- AbilitÃ  addestrate con bonus, es. Perception +5 -->  
  **Poteri della Forza:** <!-- se Force user -->
  **Equipaggiamento:** <!-- es. Blaster pistol, Comlink, Armor -->
  **Note:** <!-- Altre note, tattiche, ecc. -->

```
**Descrizione:** <% tp.file.cursor() %>  
<!-- Descrizione fisica, comportamento, storia dell'NPC -->
\*\*Affiliazione:\*\* <%* if (role) { tR += `{{role}}`; } if (affiliation) { tR += `, {{affiliation}}`; } %>.

