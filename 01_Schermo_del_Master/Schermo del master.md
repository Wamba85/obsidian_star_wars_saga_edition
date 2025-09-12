```button
name Nuovo Feat
type command
action QuickAdd: Nuovo Feat
```


`dice: 2d6+1`

```dataview
TABLE name AS Feat, prerequisites, source_book AS Source
FROM "03_Regole/03.05_Feat"
WHERE contains(prerequisites, "Strength 13")
SORT name
```

```button
name Nuovo Talento
type command
action QuickAdd: Nuovo Talento
```

# Schermo del Master – Star Wars Saga Edition

## Azioni in Combattimento
- **Azione Standard:** Attacco singolo, Usare un potere della Forza, Secondo Vento, etc.  
- **Azione di Movimento:** Muoversi fino alla velocità, estrarre un oggetto, alzarsi da prono...  
- **Azione Rapida (Swift):** Cambiare impostazione arma (stun/kill), recuperare uno scudo energetico, ecc. (3 rapide = 1 movimento)  
- **Azione di Reazione:** Attacco di opportunità, talenti come **Schivare** (Elusive Target), ecc. (si possono fare quando permesso)  
- **Azione Completa:** Attacco completo (più attacchi se BAB >= +6), Ritirata totale, Corse (x4 velocità)  

> **Attacco Opportunità:** 1 per round per nemico, trigger: un bersaglio adiacente fa azione che lo provoca (es. muoversi senza fare passo indietro, usare skill distrattamente). In Saga, muoversi fuori da un quadretto minacciato provoca AO, **ma muoversi dentro l’area minacciata no**. Usare un potere della Forza a contatto nemico provoca AO (tranne se specificato diversamente).

## Condizioni e Track
- **Condizione Indebolito (-1 passo):** -1 a tiri attacco, difese e prove abilità. Ogni condizione aggiuntiva cumula fino a -5 passi.
- **Condizione Esausto (-5 passi):** quando i malus arrivano a 5 passi di condizione, il personaggio è *esausto* e *incosciente*. 
- **Track delle Condizioni:** 5 passi negativi: -1, -2, -5, -10, -20 a attacchi/difese. A -5 il PG sviene.
- **Recupero Condizioni:** Secondo Vento rimuove -1 passo; Cure mediche possono rimuovere più passi; un riposo esteso rimuove tutti.
- **Prono:** -5 attacchi da prono; i nemici ottengono +5 attaccandoti in mischia, ma -5 con attacchi a distanza contro di te. Alzarsi = azione di movimento che provoca AO.
- **Copertura:** vedi sezione successiva.

## Coperture e Occultamento
- **Mezza Copertura:** +5 Reflex Defense (es: dietro angolo parete, metà corpo coperto).
- **Copertura Migliorata:** +10 Reflex (es: feritoia stretta, 90% corpo coperto). 
- **Copertura Totale:** Non bersagliabile direttamente (es: completamente dietro un muro solido).
- **Occultamento Parziale:** 20% miss chance ai colpi (es: penombra, fumo leggero).
- **Occultamento Totale:** 50% miss chance (es: buio totale, invisibilità). Serve percepire bersaglio con altro senso per attaccare corretto quadrello.
- *Nota:* Copertura e Occultamento non sommano; si applica il migliore dei due.

## Tipiche CD delle Abilità
- **Facile (DC 5-10):** Azioni banali (saltare piccolo ostacolo, convincere civile già ben disposto).
- **Moderato (DC 15):** Sfide comuni (scassinare lucchetto semplice, scalare albero).
- **Difficile (DC 20):** Sfide serie per personaggi medi (riparare droide danneggiato, convincere guardia sospettosa).
- **Molto Difficile (DC 25):** Richiede abilità notevole (scassinare serratura di sicurezza, acrobazia complessa).
- **Eroico (DC 30+):** Solo i migliori riescono (saltare fra due tetti lontani, hackerare sistema militare top-secret).
- *(Saga Edition usa DC fisse in molti casi, ma il GM può adattare in base alle circostanze.)*

## Effetti dei Colpi Critici
- **Tiro Naturale 20:** Colpo critico se il totale dell’attacco supera la Difesa del bersaglio:contentReference[oaicite:25]{index=25}. Danno raddoppiato.
- **Zona di Minaccia:** Alcune armi hanno minaccia 19-20. In Saga **non serve tiro di conferma**: un 19-20 che colpisce è critico.
- **Colpo Critico:** Danno raddoppiato *dopo* aver sommato tutti i bonus. Gli effetti addizionali (es. talenti come “Trip Attack” su critico) si applicano ora.
- **Condizione Assalto:** Se un singolo attacco infligge danni >= soglia danni del bersaglio, il bersaglio scende di -1 sul track condizioni oltre al danno normale (chiamato *Assault*). Un critico facilita raggiungere la soglia.

## Iniziativa e Ordine di Combattimento
- **Tiro Iniziativa:** 1d20 + bonus iniziativa (Dex mod + eventuali talenti/feat). I PG possono ritardare o preparare azioni come di consueto.
- **Parità di Iniziativa:** in caso di pareggio, confronto i bonus iniziativa (chi ha Dex maggiore agisce prima). Se ancora pari, decidere casualmente.
- **Round di Sorpresa:** se alcuni partecipanti sono sorpresi, saltano il primo round (possono compiere solo azioni di reazione).
- **Sequenza Round:** Ogni round tutti hanno 1 standard, 1 movimento, 1 swift (possono scambiarne: 2 swift -> 1 movimento, 3 swift -> 1 standard). Free actions illimitate se ragionevoli.

## Scala Personaggio vs Veicolo/Astronave
- **Danno a Veicoli/Astronavi:** Armi da personaggio infliggono 1/2 danno a veicoli di taglia Colossale e superiori (Saga Edition regola “Scale”). Armi senza danno sufficiente potrebbero non penetrarne la DR.
- **Taglie e Modificatori:** Differenza di 2 categorie di taglia dà tipicamente +5 a colpire per il più piccolo contro il più grande (il grande è facile da colpire). Esempio: Personaggio (Media) vs AT-ST (Grande): +5 al personaggio per colpire l’AT-ST. (Questa regola è usata in alcune varianti – il GM può adottarla se necessario bilanciare).
- **Combattimento Astronavale:** I turni durano 1 minuto. In ogni round di combattimento spaziale:
  1. **Fase Ingegneria:** i membri equipaggio usano abilità (Mechanics per riparare scudi, ecc.).
  2. **Fase Pilota:** tiri di Pilot contrapposti per manovrare (chi vince sceglie chi muove per primo). Poi ogni pilota può muovere il proprio veicolo fino alla sua velocità.
  3. **Fase Attacco:** gli artiglieri sparano le armi; risolvere attacchi normalmente vs difese delle navi.
- **Inseguimenti:** per inseguimenti cinematici, usare skill challenge con Pilot: una serie di tiri contrapposti dove differenza di successo accumula vantaggio/incremento distanza.

## Tabelle di Riferimento Rapido
**Bonus/Malus Taglia (creature):** Fine, -20; Minuscola, -5; Piccola, -5; Media, +0; Grande, +5; Enorme, +5; Mastodontica, +10; Colossale, +10 (applicare a tiri per colpire e Stealth: piccole ottengono bonus a Stealth ma malus a essere colpite, e viceversa):contentReference[oaicite:26]{index=26}:contentReference[oaicite:27]{index=27}.

**Punti Forza (Force Points):** Ricarica per livello (5 + metà del nuovo livello). Spenderne 1 aumenta un tiro d20 di 1d6 (o 2d6 dal livello 8, 3d6 dal 15). Un PG lato oscuro li chiama *Dark Side Points* e li spende per poteri oscuri.

**Second Wind (Secondo Vento):** 1/combattimento, azione rapida, recupera quantità di HP pari alla metà dei propri (se HP scesi sotto metà). Feat o talenti possono concedere usi extra.

**Copertura di Scudo Energetico:** Se un personaggio impugna uno **Shield** (scudo energetico portatile), aggiunge cover parziale in base al tipo: ad es. *Shield, energy* dà +2 Reflex fintanto direzionato verso attacchi frontali, etc. *(Vedi note armature.)*

*… (Altre regole specifiche possono essere aggiunte qui, come ad es. effetti di danni da esplosioni, uso esteso di abilità in situazioni particolari, etc.)*

---

**Link utili nel Vault:** [[03_Regole/03.04_Talenti]] • [[03_Regole/03.05_Feat]] • [[03_Regole/03.06_Poteri_della_Forza]] • [[05_Bestiario]] • [[06_Luoghi]] • [[07_Personaggi_PG]] • [[08_Personaggi_NPC]]
