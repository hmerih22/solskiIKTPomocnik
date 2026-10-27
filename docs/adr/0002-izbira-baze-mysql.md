---
status: sprejeta
date: 2026-10-23
---

# Relacijska baza MySQL

## Kontekst in opis problema

Podatki so izrazito povezani: rezervacija pripada uporabniku in opremi, oprema učilnici, prijava težave pa prijavitelju, odgovornemu skrbniku ter opremi in/ali učilnici. Pravila zahtevajo enolične vrednosti (e-pošta, inventarna številka, oznaka učilnice), referenčno celovitost in atomarne operacije, ki preprečijo dvojno rezervacijo ali dvojni prevzem prijave.


## Obravnavane možnosti

* MySQL
* PostgreSQL
* SQLite

## Izid odločitve

MySQL, ker podpira relacije in transakcije ter je primerna za povezane podatke načrtovane aplikacije. SQLite je primernejši za enostavno lokalno rabo, PostgreSQL pa bi bil prav tako ustrezen, a za obseg projekta ne prinaša odločilne prednosti.

### Posledice

* Dobro, ker baza sama zavrne neveljavne povezave in podvojene enolične vrednosti, tudi če aplikacija vsebuje napako.
* Dobro, ker transakcije in zaklepanje vrstic omogočajo varno sočasno ustvarjanje rezervacij.
* Dobro, ker je MySQL razširjen, dobro dokumentiran in podprt pri večini ponudnikov gostovanja.
* Slabo, ker MySQL nima izključitvenih omejitev za časovne intervale, zato mora prekrivanje preprečevati aplikacija s pravilnim zaklepanjem.
* Slabo, ker `DATETIME` ne hrani časovnega pasu; dogovor o UTC in pretvorbo v Europe/Ljubljana mora dosledno izvajati zaledje.
* Slabo, ker je za razvoj in teste potreben delujoč MySQL strežnik, kar je zahtevnejše od datotečne baze.
