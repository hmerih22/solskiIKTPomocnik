# Zasnova rešitve

## Ime rešitve

Šolski IKT pomočnik – rezervacije opreme in prijava težav

## Osnovna ideja

Šolski IKT pomočnik je spletna aplikacija za rezervacijo skupne šolske opreme ter prijavo in obravnavo tehničnih težav. Namenjena je uporabi znotraj ene šole. Združuje pregled razpoložljivosti opreme, rezervacije in evidenco težav na enem mestu.

Učitelji lahko rezervirajo prenosnike, projektorje ali komplete tablic ter prijavijo težavo na posameznem kosu opreme ali IKT težavo v učilnici. IKT skrbnik spremlja prijave in vodi njihovo obravnavo, administrator pa upravlja uporabnike, učilnice in evidenco opreme.

## Namen rešitve in problem, ki ga naslavlja

Kadar se rezervacije in prijave težav urejajo prek ustnih dogovorov, elektronske pošte ali ločenih seznamov, je težko zagotoviti enoten pregled. Več učiteljev lahko načrtuje uporabo iste opreme v istem času, prijava težave pa lahko ostane brez jasnega podatka o tem, kdo jo rešuje in ali je že odpravljena.

Aplikacija bo naslavljala naslednje probleme:

- pomanjkanje skupnega pregleda razpoložljive opreme in rezervacij;
- prekrivanje rezervacij iste opreme;
- nepregledno oddajanje in spremljanje prijav tehničnih težav;
- nejasno odgovornost za obravnavo posamezne prijave;
- rezerviranje opreme, ki je označena kot nedelujoča.

Namen rešitve je olajšati načrtovanje uporabe opreme in omogočiti sledljivo obravnavo težav. Učitelj bo lahko preveril, ali je oprema prosta, ter spremljal stanje svoje prijave. IKT skrbnik bo imel skupen pregled prijav, njihovega stanja in zapisanih rešitev.

## Ciljni uporabniki

| Uporabniška vloga | Situacija uporabe | Namen uporabe |
| --- | --- | --- |
| Učitelj | Priprava pouka in pojav tehnične težave med delom | Rezervacija opreme, prijava težave in spremljanje njene obravnave |
| IKT skrbnik | Organizacija in izvajanje tehnične podpore v šoli | Pregled in prevzem prijav, beleženje rešitev ter označevanje nedelujoče opreme |
| Administrator | Vzdrževanje uporabniških računov in osnovnih evidenc | Upravljanje uporabnikov, njihovih vlog, učilnic in opreme |

Aplikacija bo dostopna prijavljenim uporabnikom prek spletnega brskalnika. Uporabniške račune bo ustvarjal administrator. Posamezne možnosti bodo dostopne glede na uporabniško vlogo.

## Kratek opis delovanja

### Rezervacija opreme

Učitelj po prijavi izbere opremo ter datum, začetni in končni čas uporabe. Sistem preveri, ali je oprema uporabna in ali se izbrani termin prekriva z drugo aktivno rezervacijo iste opreme. Če je termin prost, shrani rezervacijo in prikaže potrditev. Če rezervacija ni mogoča, uporabniku pojasni razlog. Učitelj lahko pregleduje in prekliče svoje prihodnje rezervacije.

Posamezna rezervacija se nanaša na eno evidentirano enoto opreme. Komplet tablic se lahko evidentira kot ena enota, ki se rezervira v celoti.

### Prijava in obravnava težav

Učitelj pri oddaji prijave izbere opremo in/ali učilnico ter vnese naslov in opis težave. Prijava na opremi se lahko nanaša na primer na projektor, ki se ne vklopi. Prijava IKT težave v učilnici pa se lahko nanaša na nedelujočo internetno povezavo, ne da bi bila težava vezana na določen kos opreme.

Nova prijava se prikaže IKT skrbniku. Skrbnik jo prevzame, s čimer postane odgovoren za njeno obravnavo, in spremeni stanje iz »nova« v »v obravnavi«. Po odpravi težave zapiše rešitev in prijavo označi kot »rešena«. Prijavitelj lahko spremlja stanje svoje prijave in prebere zapisano rešitev.

Če IKT skrbnik ugotovi, da oprema ni uporabna, jo označi kot nedelujočo. Sistem prepreči nove rezervacije te opreme, pri obstoječih prihodnjih rezervacijah pa prikaže opozorilo za nadaljnjo ureditev. Po odpravi napake lahko skrbnik opremo ponovno označi kot uporabno.

## Primer uporabe

Učitelj za sredo med 9.00 in 10.00 rezervira komplet tablic. Sistem preveri razpoložljivost in potrdi rezervacijo. Drugemu učitelju, ki želi isti komplet rezervirati med 9.30 in 10.30, sistem rezervacijo zavrne zaradi prekrivanja terminov.

Med poukom prvi učitelj ugotovi, da se tablice v učilnici 12 ne povežejo z omrežjem. Odda prijavo z navedbo učilnice, kompleta tablic in opisom težave. IKT skrbnik prijavo prevzame, preveri vzrok in odpravi težavo. Nato zapiše rešitev ter zaključi prijavo. Učitelj ob pregledu svoje prijave vidi, da je težava rešena.
