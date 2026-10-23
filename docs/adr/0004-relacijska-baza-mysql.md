---
status: sprejeta
date: 2026-10-23
---

# Relacijska baza MySQL

## Kontekst in opis problema

Podatki so izrazito povezani: rezervacija pripada uporabniku in opremi, oprema učilnici, prijava težave pa prijavitelju, odgovornemu skrbniku ter opremi in/ali učilnici. Pravila zahtevajo enolične vrednosti (e-pošta, inventarna številka, oznaka učilnice), referenčno celovitost in atomarne operacije, ki preprečijo dvojno rezervacijo ali dvojni prevzem prijave.

Katera vrsta podatkovne baze zanesljivo uveljavi povezave, omejitve in transakcije, ki jih zahtevajo pravila sistema?

## Obravnavane možnosti

* MySQL 8.4 z InnoDB
* PostgreSQL
* SQLite
* Dokumentna baza (npr. MongoDB)

## Izid odločitve

Izbrana možnost: »MySQL 8.4 z InnoDB«, ker relacijski model neposredno izrazi pet povezanih entitet s tujimi ključi in enoličnimi omejitvami. InnoDB podpira transakcije in zaklepanje vrstic (`SELECT ... FOR UPDATE`), na katerih temelji preprečevanje prekrivanj ([ADR-0008](0008-transakcije-z-zaklepanjem-pri-kljucnih-operacijah.md)). PostgreSQL bi bil tehnično enakovreden ali celo boljši, saj podpira izključitvene omejitve za intervale. MySQL smo izbrali, ker je razvijalcu bolj poznan in ker sta MySQL Workbench in šolska infrastruktura že na voljo. SQLite ni primeren za sočasne zapise več uporabnikov. Dokumentna baza ne bi uveljavila povezav in bi pravila doslednosti prenesla v aplikacijo.

### Posledice

* Dobro, ker baza sama zavrne neveljavne povezave in podvojene enolične vrednosti, tudi če aplikacija vsebuje napako.
* Dobro, ker transakcije in zaklepanje vrstic omogočajo varno sočasno ustvarjanje rezervacij.
* Dobro, ker je MySQL razširjen, dobro dokumentiran in podprt pri večini ponudnikov gostovanja.
* Slabo, ker MySQL nima izključitvenih omejitev za časovne intervale, zato mora prekrivanje preprečevati aplikacija s pravilnim zaklepanjem.
* Slabo, ker `DATETIME` ne hrani časovnega pasu; dogovor o UTC in pretvorbo v Europe/Ljubljana mora dosledno izvajati zaledje.
* Slabo, ker je za razvoj in teste potreben delujoč MySQL strežnik, kar je zahtevnejše od datotečne baze.
