---
type: species
name: "<% tp.file.title %>"
ability_modifiers: ""
size: "<%* let size = await tp.system.suggester(['Small','Medium','Large'], ['Small','Medium','Large']); tR += size %>"
speed: "6"  # valore predefinito piÃ¹ comune
traits: []
languages: []
source_book: "<%* let sb = await tp.system.prompt('Manuale (es: SECR)'); tR += sb %>"
page: "<%* let pg = await tp.system.prompt('Pagina'); tR += pg %>"
tags: [SWSE, Species]
slug: "<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') %>"
source_url: ""
source_license: "CC BY-SA 3.0 (Fandom)"
import_hash: ""
last_imported: <% tp.date.now("YYYY-MM-DD") %>
---

**Modificatori:** <% tp.file.cursor() %>  
**Taglia:** <%* if (size) { tR += `{{size}}`; } %> â€“ **VelocitÃ :** 6 caselle  
**Tratti speciali:** <small>(vedi sotto)</small>  

**Descrizione:**  
<!-- Descrizione della specie, cultura, ecc. -->  

- **Lingue:** <!-- Elencare le lingue tipiche -->  
- **Bonus linguaggi bonus:** <!-- Lingue bonus se Int > 12, ecc. -->

*Fonte:* <%* if (sb) { tR += `{{sb}}`; } if (pg) { tR += `, p.{{pg}}`; } %>.

