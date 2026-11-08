# Funkcionalnosti in obseg rešitve

## Uporabniške vloge in pravice

Aplikacija je namenjena eni šoli in dostopna samo prijavljenim uporabnikom. Vsak uporabnik ima eno od treh vlog. IKT skrbnik ima tudi pravice učitelja, administrator pa pravice obeh drugih vlog.

### Učitelj

- Pregleduje opremo, njeno lokacijo, stanje in razpoložljivost za izbrani termin.
- Ustvarja rezervacije zase ter pregleduje in preklicuje svoje prihodnje rezervacije.
- Prijavlja težave na opremi ali IKT težave v učilnici.
- Pregleduje svoje prijave, njihovo stanje, odgovornega skrbnika in zapisano rešitev.
- Ne spreminja rezervacij drugih uporabnikov, stanja opreme, obravnave prijav ali uporabniških vlog.

### IKT skrbnik

- Ima vse pravice učitelja.
- Pregleduje vse prijave težav in vse rezervacije.
- Prevzema nove prijave ter vodi obravnavo prijav, za katere je odgovoren.
- Zapisuje rešitve in zaključuje prevzete prijave.
- Označuje opremo kot uporabno ali nedelujočo.
- Prekliče prihodnjo rezervacijo nedelujoče opreme in zapiše razlog preklica, ki ga vidi njen lastnik.
- Ne upravlja uporabniških računov, vlog ali osnovnih evidenc učilnic in opreme.

### Administrator

- Ima vse pravice učitelja in IKT skrbnika.
- Ustvarja in deaktivira uporabniške račune ter določa uporabniške vloge.
- Dodaja in ureja učilnice ter opremo, vključno z inventarno številko, vrsto in lokacijo.
- Pregleduje vse rezervacije in prijave ter po potrebi prekliče prihodnjo rezervacijo z zapisanim razlogom.
- Po potrebi prerazporedi prijavo drugemu IKT skrbniku ali jo zaključi z zapisano rešitvijo.

Pravice se preverjajo na zaledju pri vsaki zaščiteni operaciji. Skrivanju gumbov v uporabniškem vmesniku mora slediti tudi preverjanje dovoljenj ob obdelavi zahteve.

## Predvidene funkcionalnosti

MVP pomeni prvo delujočo različico aplikacije. Predvidenih je 12 vsebinskih funkcionalnosti; prvih sedem bo vključenih v MVP.

| ID | Funkcionalnost | Opis | Obseg |
| --- | --- | --- | --- |
| F01 | Pregled opreme in uporabnosti | Uporabnik vidi naziv, inventarno številko, vrsto, lokacijo in stanje opreme. | MVP |
| F02 | Preverjanje razpoložljivosti | Uporabnik izbere opremo in termin; sistem prikaže, ali je oprema uporabna in prosta. | MVP |
| F03 | Rezervacija brez prekrivanja | Sistem ob potrditvi ponovno preveri termin in shrani rezervacijo samo, če ni prekrivanja z drugo aktivno rezervacijo iste opreme. | MVP |
| F04 | Pregled in preklic rezervacij | Učitelj spremlja svoje rezervacije in prekliče prihodnjo rezervacijo. Skrbnik in administrator imata dodatne pravice, opisane pri vlogah. | MVP |
| F05 | Prijava in spremljanje težave | Učitelj odda opis težave z navedbo opreme in/ali učilnice ter spremlja stanje, odgovornega skrbnika in rešitev. | MVP |
| F06 | Prevzem in obravnava prijave | IKT skrbnik prevzame novo prijavo, jo obravnava in zaključi z zapisano rešitvijo. | MVP |
| F07 | Izločitev nedelujoče opreme | Skrbnik označi opremo kot nedelujočo; sistem prepreči nove rezervacije in opozori na obstoječe prihodnje rezervacije. | MVP |
| F08 | Evidenca prevzema in vračila | Sistem beleži dejanski prevzem in vračilo rezervirane opreme ter omogoča pregled zamud pri vračilu. | Nadgradnja |
| F09 | Komentarji pri prijavi | Prijavitelj in skrbnik izmenjujeta dodatne informacije v pogovoru, vezanem na prijavo. | Nadgradnja |
| F10 | Fotografije in priponke | Prijavitelj lahko prijavi priloži fotografijo napake ali drugo relevantno datoteko. | Nadgradnja |
| F11 | Obvestila po e-pošti | Uporabnik prejme obvestilo o potrditvi ali preklicu rezervacije in spremembi stanja svoje prijave. | Nadgradnja |
| F12 | Statistika uporabe in težav | Skrbnik za izbrano obdobje pregleda število rezervacij, pogostost prijav po opremi in učilnicah ter čas reševanja. | Nadgradnja |

## Obseg prve delujoče različice (MVP)

MVP vključuje F01–F07. Te funkcionalnosti omogočajo celoten osnovni potek od rezervacije opreme do prijave in odprave težave.

Poleg njih so za delovanje vključene tehnične osnove: prijava in odjava, preverjanje treh uporabniških vlog, upravljanje uporabniških računov, osnovnih evidenc učilnic in opreme ter shranjevanje v podatkovno bazo MySQL. Te osnove se ne štejejo med sedem vsebinskih MVP funkcionalnosti. Zaledje bo izdelano s Flaskom, uporabniški vmesnik pa s HTML, CSS in Jinja predlogami; podrobnosti so predmet dokumenta o arhitekturi.

### Pravila rezervacij

- Rezervacija se nanaša na eno evidentirano enoto opreme. Komplet tablic se lahko evidentira kot ena enota in rezervira v celoti.
- Rezervacijo ustvari prijavljeni uporabnik zase.
- Začetek mora biti v prihodnosti in pred koncem rezervacije. Uporabnik vnese datum in čas začetka ter konca.
- Dve aktivni rezervaciji iste opreme se ne smeta prekrivati. Če se ena konča ob 10.00, se druga lahko začne ob 10.00.
- Preklicana rezervacija ne zaseda termina. Pretekle in preklicane rezervacije ostanejo v evidenci.
- Učitelj lahko prekliče svojo rezervacijo, dokler se še ni začela.
- Rezervacija je ob uspešni oddaji potrjena samodejno; dodatno odobravanje ni predvideno.
- Preverjanje prekrivanja in shranjevanje morata preprečiti dvojno rezervacijo tudi ob sočasni oddaji zahtev dveh uporabnikov.

### Pravila prijav in obravnave

- Prijava mora imeti naslov in opis ter biti povezana z opremo ali učilnico; lahko je povezana z obema.
- Nova prijava ima stanje »nova« in še nima odgovornega skrbnika.
- Ob prevzemu se shrani odgovorni skrbnik in stanje spremeni v »v obravnavi«. Ista prijava ima največ enega odgovornega skrbnika.
- Odgovorni skrbnik prijavo zaključi s stanjem »rešena«. Pred zaključkom mora vnesti opis rešitve; sistem shrani čas zaključka.
- Učitelj svoje oddane prijave v MVP ne spreminja ali briše. Administratorska prerazporeditev prijave je dovoljena v okviru navedenih pravic.
- Označitev opreme kot nedelujoče je ločena odločitev skrbnika. Vsaka prijava težave ne pomeni samodejno, da je oprema neuporabna.
- Pri nedelujoči opremi se nove rezervacije zavrnejo. Obstoječe prihodnje rezervacije ostanejo v evidenci z vidnim opozorilom; skrbnik jih lahko prekliče z razlogom.
- Zaključek prijave samodejno ne spremeni stanja opreme. Skrbnik po preverjanju opremo posebej označi kot uporabno.

### Vsebinska zahtevnost MVP

F03, F06 in F07 vsebujejo domensko logiko, ki presega osnovno dodajanje, urejanje in brisanje podatkov:

- **F03:** preverjanje časovnega prekrivanja in preprečevanje dvojnih rezervacij;
- **F06:** prevzem odgovornosti, dovoljeni prehodi med stanji in obvezen zapis rešitve;
- **F07:** vpliv uporabnosti opreme na nove in obstoječe rezervacije.

### Preverjanje prve različice

MVP bo mogoče predstaviti z naslednjimi primeri:

1. Učitelj uspešno rezervira prost projektor.
2. Drugi učitelj istega projektorja ne more rezervirati v prekrivajočem se terminu, tudi ob sočasni oddaji zahtev.
3. Preklic rezervacije sprosti termin; rezervacija, ki se začne ob koncu druge, je dovoljena.
4. Učitelj odda težavo, vezano samo na učilnico, in drugo težavo, vezano na opremo.
5. IKT skrbnik prevzame prijavo in jo zaključi z rešitvijo; brez rešitve zaključek ni mogoč.
6. Nedelujoče opreme ni mogoče na novo rezervirati, pri že obstoječi prihodnji rezervaciji pa je prikazano opozorilo.
7. Učitelj ne more preklicati tuje rezervacije ali spremeniti stanja prijave, tudi če neposredno pošlje zahtevo zaledju.

## Kasnejše nadgradnje

Po dokončanju MVP so predvidene naslednje možnosti nadaljnjega razvoja:

1. **Prevzem in vračilo opreme (F08):** spremljanje dejanske izposoje in zamud.
2. **Komentarji pri prijavah (F09):** dopolnjevanje informacij in komunikacija znotraj prijave.
3. **Fotografije in priponke (F10):** lažja ponazoritev tehnične težave.
4. **E-poštna obvestila (F11):** obveščanje brez stalnega odpiranja aplikacije.
5. **Statistika (F12):** pregled uporabe opreme, ponavljajočih se težav in časa obravnave.

Te funkcionalnosti niso pogoj za dokončanje prve različice projekta.

## Funkcionalnosti zunaj obsega projekta

Naslednje funkcionalnosti niso vključene v ta projekt in niso del načrtovanih nadgradenj F08–F12:

- **Povezovanje z eAsistentom ali drugimi šolskimi sistemi:** uporabniki in učilnice se vodijo znotraj aplikacije.
- **Samodejno zaznavanje IKT napak:** sistem ne spremlja omrežja ali naprav in sam ne odkriva težav; prijave oddajo uporabniki.
- **Upravljanje nabave in servisnih stroškov:** aplikacija ne vodi naročil, računov, garancijskih postopkov ali finančnega poslovanja.
- **Podpora več šolam:** rešitev je zasnovana za eno šolo in ne ločuje podatkov več ustanov.
- **Samostojna mobilna aplikacija:** uporaba poteka prek spletnega brskalnika.
