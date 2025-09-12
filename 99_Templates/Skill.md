---
type: skill
name: "<% tp.file.title %>"
ability: "<%* let abil = await tp.system.prompt('Caratteristica (Str/Dex/Con/Int/Wis/Cha)'); tR += abil %>"
trained_only: false
armor_check_penalty: false
special: ""
description: ""
source_book: "SECR"
page: ""
tags: [SWSE, Skill]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Descrizione:** <% tp.file.cursor() %>

- **Usi comuni:** <!-- elencare gli utilizzi tipici e CD -->
- **Speciale:** <!-- eventuali regole speciali aggiuntive -->

*AbilitÃ  chiave:* <%* if (abil) { tR += `{{abil}}`; } %>. <%* if (trained_only) { tR += `*(Solo addestrato)*`; } %><%* if (armor_check_penalty) { tR += ` *(PenalitÃ  armatura si applica)*`; } %>.

