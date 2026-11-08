# Uporabniške zgodbe

## US-01: Pregled opreme

- **Povezana funkcionalnost:** F01 – Pregled opreme in uporabnosti
- **Uporabniška vloga:** Učitelj

**Zgodba:** Kot učitelj želim pregledati šolsko opremo in njeno stanje, da lahko izberem ustrezno opremo za pouk.

**Sprejemni kriteriji:**

1. Prijavljen učitelj pri vsaki enoti vidi naziv, inventarno številko, vrsto, običajno lokacijo in stanje uporabnosti.
2. Stanje »uporabna« ali »nedelujoča« je prikazano z besedilom; uporabniku ga ni treba razbrati samo iz barve.
3. Nedelujoča oprema ostane vidna na seznamu in je označena kot neprimerna za novo rezervacijo.
4. Če ni evidentirane opreme, se namesto vrstic seznama prikaže sporočilo »Ni evidentirane opreme«.

## US-02: Preverjanje prostega termina

- **Povezana funkcionalnost:** F02 – Preverjanje razpoložljivosti
- **Uporabniška vloga:** Učitelj

**Zgodba:** Kot učitelj želim preveriti razpoložljivost opreme za izbrani termin, da lahko načrtujem njeno uporabo pri pouku.

**Sprejemni kriteriji:**

1. Pri uporabni opremi in veljavnem prihodnjem terminu brez prekrivajočih aktivnih rezervacij sistem prikaže, da je oprema prosta; preverjanje samo ne ustvari rezervacije.
2. Če obstaja aktivna rezervacija 9.00–10.00, sistem isti termin in termin 9.30–10.30 istega dne prikaže kot zaseden, termin 10.00–11.00 pa kot prost, če ni drugih rezervacij.
3. Preklicana rezervacija ne povzroči prikaza zasedenega termina.
4. Pri nedelujoči opremi sistem prikaže, da je ni mogoče rezervirati, tudi če nima rezervacij.
5. Pri začetku v preteklosti ali začetku, ki ni pred koncem, sistem prikaže napako pri terminu in ne prikaže potrditve razpoložljivosti.
## US-03: Ustvarjanje rezervacije

- **Povezana funkcionalnost:** F03 – Rezervacija brez prekrivanja
- **Uporabniška vloga:** Učitelj


**Zgodba:** Kot učitelj želim rezervirati prosto opremo za določen termin, da bo njena načrtovana uporaba evidentirana in termin zaseden zame.

**Sprejemni kriteriji:**

1. Ob oddaji veljavnega prihodnjega termina za uporabno in prosto opremo sistem ustvari eno aktivno rezervacijo, povezano s prijavljenim uporabnikom in izbrano opremo, ter prikaže potrditev.
2. Ob oddaji sistem ponovno preveri razpoložljivost; če je termin med preverjanjem in oddajo zasedel drug uporabnik, rezervacije ne ustvari in prikaže konflikt.
3. Dve sočasni zahtevi za prekrivajoča termina iste opreme ne moreta ustvariti dveh aktivnih rezervacij; ena uspe, druga prejme zavrnitev zaradi zasedenosti.
4. Neveljaven termin ali nedelujoča oprema povzroči zavrnitev brez novega zapisa rezervacije.
5. Rezervacija, ki se začne natanko ob koncu obstoječe rezervacije, je dovoljena, če so izpolnjena ostala pravila.

## US-04: Pregled in preklic rezervacij

- **Povezana funkcionalnost:** F04 – Pregled in preklic rezervacij
- **Uporabniška vloga:** Učitelj; dodatne pravice imata IKT skrbnik in administrator

**Zgodba:** Kot učitelj želim pregledati svoje rezervacije in preklicati prihodnjo rezervacijo, ki je ne potrebujem, da sprostim opremo za druge uporabnike.

**Sprejemni kriteriji:**

1. Učitelj v svojem pregledu vidi lastne prihodnje, pretekle in preklicane rezervacije z opremo, terminom in statusom.
2. Učitelj lahko prekliče svojo aktivno rezervacijo samo pred njenim začetkom; sistem shrani status »preklicana«, čas preklica in preklicatelja ter sprosti termin.
3. Poskus učiteljevega preklica tuje, že začete ali že preklicane rezervacije se zavrne brez spremembe podatkov, tudi pri neposredni zahtevi zaledju.
4. IKT skrbnik lahko prekliče prihodnjo aktivno rezervacijo nedelujoče opreme, administrator pa katerokoli prihodnjo aktivno rezervacijo. Oba morata vnesti neprazen razlog.
5. Lastnik preklicane rezervacije vidi razlog, kadar je bil vnesen; zapis rezervacije se ne izbriše.

## US-05: Prijava in spremljanje težave

- **Povezana funkcionalnost:** F05 – Prijava in spremljanje težave
- **Uporabniška vloga:** Učitelj

**Zgodba:** Kot učitelj želim prijaviti težavo na opremi ali v učilnici in spremljati njeno stanje, da vem, ali je bila težava prevzeta in odpravljena.

**Sprejemni kriteriji:**

1. Sistem sprejme prijavo z nepraznim naslovom in opisom ter izbrano opremo, učilnico ali obema; brez obeh povezav oddajo zavrne.
2. Ob uspešni oddaji shrani prijavljenega uporabnika kot prijavitelja, čas oddaje in status »nova«; odgovorni skrbnik še ni določen.
3. Učitelj na seznamu svojih prijav vidi naslov, datum in stanje, pri podrobnostih pa opis ter odgovornega skrbnika, ko je določen.
4. Pri rešeni prijavi učitelj vidi zapisano rešitev in čas zaključka.
5. Učitelj ne more brati podrobnosti tuje prijave ali spremeniti oziroma izbrisati oddane prijave, tudi z neposredno zahtevo zaledju.

## US-06: Prevzem in rešitev prijave

- **Povezana funkcionalnost:** F06 – Prevzem in obravnava prijave
- **Uporabniška vloga:** IKT skrbnik; administrator ima dodatne pravice

**Zgodba:** Kot IKT skrbnik želim prevzeti prijavo in zabeležiti njeno rešitev, da je jasno, kdo težavo obravnava in kako je bila odpravljena.

**Sprejemni kriteriji:**

1. IKT skrbnik vidi vse prijave z naslovom, prijaviteljem, opremo in/ali učilnico, stanjem in odgovornim skrbnikom, če je določen.
2. Ob prevzemu nove prijave sistem določi prijavljenega skrbnika kot odgovorno osebo, zabeleži čas prvega prevzema in spremeni stanje v »v obravnavi«.
3. Če dva skrbnika sočasno prevzameta isto novo prijavo, sistem potrdi samo en prevzem; drugi prejme informacijo, da je prijava že prevzeta.
4. Odgovorni skrbnik lahko svojo prijavo v obravnavi zaključi le z neprazno rešitvijo; sistem nato shrani stanje »rešena« in čas zaključka. Drugi skrbnik take prijave ne more zaključiti.
5. Administrator lahko prijavo v obravnavi prerazporedi aktivnemu IKT skrbniku ali administratorju in ohrani čas prvega prevzema; lahko jo tudi zaključi z neprazno rešitvijo. Učitelju se te operacije zavrnejo.

## US-07: Označevanje nedelujoče opreme

- **Povezana funkcionalnost:** F07 – Izločitev nedelujoče opreme
- **Uporabniška vloga:** IKT skrbnik

**Zgodba:** Kot IKT skrbnik želim nedelujočo opremo označiti kot neuporabno za rezervacije, da učitelji ne načrtujejo uporabe pokvarjene opreme.

**Sprejemni kriteriji:**

1. IKT skrbnik ali administrator lahko spremeni stanje opreme iz »uporabna« v »nedelujoča«; učiteljev poskus se zavrne brez spremembe.
2. Po spremembi stanja sistem zavrne nove rezervacije te opreme, tudi če je bil obrazec odprt pred spremembo stanja.
3. Obstoječe prihodnje rezervacije se ne izbrišejo ali samodejno prekličejo; v njihovem pregledu in podrobnostih je vidno opozorilo, da oprema ne deluje.
4. Ko skrbnik opremo ponovno označi kot uporabno, se opozorilo odstrani in novi prosti termini so ponovno rezervabilni; prej preklicane rezervacije se ne obnovijo.
5. Oddaja ali zaključek prijave težave samodejno ne spremeni uporabnosti opreme.

## US-08: Prevzem in vračilo opreme

- **Povezana funkcionalnost:** F08 – Evidenca prevzema in vračila
- **Uporabniška vloga:** IKT skrbnik

**Zgodba:** Kot IKT skrbnik želim evidentirati dejanski prevzem in vračilo rezervirane opreme, da vem, katera oprema je izposojena in katera še ni vrnjena.

**Sprejemni kriteriji:**

1. Pri nepreklicani rezervaciji uporabne opreme lahko skrbnik zabeleži dejanski prevzem; sistem shrani trenutni čas in isto rezervacijo ne more prevzeti še enkrat.
2. Preklicane rezervacije ali rezervacije opreme, ki je že evidentirana kot izposojena pri drugi rezervaciji, ni mogoče označiti kot prevzete.
3. Vračilo je mogoče evidentirati samo po prevzemu in samo enkrat; sistem shrani čas vračila in opreme ne prikazuje več kot dejansko izposojene.
4. Rezervacija s prevzemom, brez vračila in s koncem v preteklosti je v skrbnikovem pregledu označena kot zamuda pri vračilu.

## US-09: Komentarji pri prijavi

- **Povezana funkcionalnost:** F09 – Komentarji pri prijavi
- **Uporabniška vloga:** Prijavitelj oziroma IKT skrbnik

**Zgodba:** Kot prijavitelj želim pri svoji prijavi odgovoriti skrbniku s komentarjem, da mu lahko posredujem dodatne informacije o težavi.

**Sprejemni kriteriji:**

1. Komentar lahko dodajo prijavitelj, odgovorni skrbnik in administrator; drugim uporabnikom se dodajanje zavrne.
2. Vsak dodan komentar je povezan s prijavo in ima neprazno besedilo, avtorja ter čas oddaje.
3. Dovoljeni uporabniki vidijo komentarje po času oddaje od najstarejšega do najnovejšega.
4. Pri rešeni prijavi so obstoječi komentarji berljivi, dodajanje novih pa ni dovoljeno.

## US-10: Priponka pri prijavi

- **Povezana funkcionalnost:** F10 – Fotografije in priponke
- **Uporabniška vloga:** Učitelj

**Zgodba:** Kot učitelj želim prijavi priložiti fotografijo ali dokument, da skrbnik lažje razume prikazano napako.

**Sprejemni kriteriji:**

1. Pri oddaji prijave lahko učitelj priloži do tri datoteke vrste JPEG, PNG ali PDF, vsako do vključno 5 MiB; prijava brez priponk je dovoljena.
2. Pri preseženi omejitvi števila ali velikosti oziroma nedovoljeni vrsti sistem oddajo zavrne z razlogom in ne ustvari delne prijave. Vrsta se preverja tudi glede na vsebino, ne samo končnico.
3. Sprejeta priponka je povezana s prijavo in prikazana z nazivom; prijavitelj, IKT skrbnik in administrator jo lahko odprejo.
4. Učitelj ne more dostopati do priponke tuje prijave prek neposrednega naslova datoteke. Shranjena datoteka se ne izvaja kot programska koda.

## US-11: E-poštna obvestila

- **Povezana funkcionalnost:** F11 – Obvestila po e-pošti
- **Uporabniška vloga:** Učitelj

**Zgodba:** Kot učitelj želim prejeti e-poštno obvestilo o svoji rezervaciji ali spremembi stanja prijave, da za preverjanje sprememb ne potrebujem stalno odpirati aplikacije.

**Sprejemni kriteriji:**

1. Po uspešno shranjeni novi rezervaciji sistem sproži obvestilo na e-poštni naslov lastnika z opremo in terminom.
2. Po uspešno shranjenem preklicu sistem sproži obvestilo lastniku, ki vsebuje opremo, termin in razlog, če je bil vnesen.
3. Ob prehodu prijave v »v obravnavi« ali »rešena« sistem sproži obvestilo prijavitelju z oznako prijave, novim stanjem in povezavo do njenih podrobnosti.
4. Zavrnjena ali razveljavljena operacija ne sproži obvestila o uspehu. Napaka pri pošiljanju se zabeleži, vendar ne razveljavi uspešno shranjene rezervacije ali spremembe prijave.

## US-12: Statistika uporabe in težav

- **Povezana funkcionalnost:** F12 – Statistika uporabe in težav
- **Uporabniška vloga:** IKT skrbnik

**Zgodba:** Kot IKT skrbnik želim pregledati uporabo opreme in pogostost težav v izbranem obdobju, da prepoznam najbolj obremenjeno opremo in ponavljajoče se težave.

**Sprejemni kriteriji:**

1. Statistika je dostopna IKT skrbniku in administratorju; učiteljev neposreden dostop se zavrne. Obdobje se določi z vključujočim začetnim datumom in vključujočim končnim datumom v lokalnem času; obrnjen interval se zavrne.
2. Pregled po opremi šteje nepreklicane rezervacije, katerih začetek spada v izbrano obdobje.
3. Pregled težav po opremi in učilnicah šteje prijave, oddane v obdobju. Prijava z obema povezavama se šteje v obeh ločenih razčlenitvah, v skupnem številu prijav pa samo enkrat.
4. Povprečni čas reševanja se izračuna od oddaje do zaključka za prijave, zaključene v obdobju; odprte prijave niso vključene v povprečje.
5. Če ni ustreznih podatkov, so števci nič, povprečni čas reševanja pa je označen z »Ni podatkov«.

## US-13: Prijava v aplikacijo

- **Povezana funkcionalnost:** Tehnična osnova – prijava in odjava
- **Uporabniška vloga:** Učitelj, IKT skrbnik ali administrator

**Zgodba:** Kot uporabnik želim dostopati do aplikacije s svojim računom, da lahko uporabljam funkcionalnosti, dovoljene moji vlogi.

**Sprejemni kriteriji:**

1. Aktivni uporabnik se z veljavnim e-poštnim naslovom in geslom uspešno prijavi; napačni podatki ali neaktivni račun povzročijo zavrnitev brez prijavljene seje.
2. Neprijavljeni uporabnik pri dostopu do zaščitene strani dobi zahtevo za prijavo in ne prejme zaščitenih podatkov.
3. Po odjavi zaščitene operacije niso več dovoljene brez ponovne prijave.
4. Po deaktivaciji že prijavljenega računa ali spremembi njegove vloge naslednja zaščitena zahteva upošteva novo stanje računa in pravice.

## US-14: Upravljanje uporabniških računov

- **Povezana funkcionalnost:** Tehnična osnova – računi in uporabniške vloge
- **Uporabniška vloga:** Administrator

**Zgodba:** Kot administrator želim ustvarjati račune in določati uporabniške vloge, da imajo zaposleni ustrezen dostop do sistema.

**Sprejemni kriteriji:**

1. Administrator lahko ustvari račun z imenom, priimkom, enoličnim e-poštnim naslovom, začetnim geslom in eno od treh dovoljenih vlog. Geslo se shrani samo kot varna zgoščena vrednost.
2. Pri manjkajočih obveznih podatkih, neveljavni vlogi ali že uporabljenem e-poštnem naslovu se nov račun ne ustvari in prikaže se razlog.
3. Administrator lahko spremeni vlogo ali deaktivira račun; pred odvzemom skrbniških pravic ali deaktivacijo mora prerazporediti odprte prijave, za katere je ta uporabnik odgovoren.
4. Deaktivacija ohrani povezane rezervacije in prijave. Učitelju in IKT skrbniku se upravljanje računov zavrne tudi pri neposredni zahtevi zaledju.

## US-15: Upravljanje učilnic in opreme

- **Povezana funkcionalnost:** Tehnična osnova – osnovne evidence
- **Uporabniška vloga:** Administrator

**Zgodba:** Kot administrator želim vzdrževati evidenco učilnic in opreme, da imajo uporabniki na voljo pravilne podatke za rezervacije in prijave.

**Sprejemni kriteriji:**

1. Administrator lahko doda učilnico z enolično oznako in nepraznim nazivom ter uredi njen naziv in opis.
2. Administrator lahko doda opremo z nazivom, enolično inventarno številko, vrsto, stanjem in povezavo na obstoječo učilnico oziroma prostor.
3. Podvojena oznaka učilnice, podvojena inventarna številka ali manjkajoč obvezen podatek povzroči zavrnitev brez delnega zapisa.
4. Urejanje opreme ohrani njen identifikator in povezane rezervacije ter prijave. Povezanih evidenc ni mogoče fizično izbrisati.
5. Učitelj in IKT skrbnik ne moreta dodajati ali urejati osnovnih evidenc; skrbnik lahko ločeno spreminja uporabnost opreme skladno z US-07.
