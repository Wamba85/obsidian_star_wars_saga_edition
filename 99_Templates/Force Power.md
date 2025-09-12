---
type: force_power
name: "<% tp.file.title %>"
keywords: []
time: ""
target: ""
range: ""
check: ""
description: ""
source_book: "<%* let sb = await tp.system.prompt('Fonte (es: SECR, FUCG)'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Force Power]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Tipo:** <% tp.file.cursor() %>  
**Tempo:**  _(azione necessaria per utilizzare il potere)_  
**Bersaglio:**  _(bersaglio/area)_  
**Range:**  _(portata in quadretti/metri)_  
**Prova:**  _(Use the Force vs difesa avversario o CD)_  

**Descrizione:**  
<!-- Descrizione dettagliata degli effetti del potere, con eventuali risultati variabili in base al tiro. -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, pag. {{pg}}`; } %>.

