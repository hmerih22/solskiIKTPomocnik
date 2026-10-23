---
status: sprejeta
date: 2026-10-23
---

# Parametrizirane SQL-poizvedbe brez ORM

## Kontekst in opis problema

Ključne operacije, na primer ustvarjanje rezervacije in prevzem prijave, so odvisne od natančnega vedenja poizvedb: zaklepajočega branja, pogojnih posodobitev in vrstnega reda v transakciji. Hkrati mora biti dostop do podatkov varen pred vrivanjem SQL in ločen od poti ter predlog.

Ali naj aplikacija do baze dostopa prek ORM ali z lastnimi SQL-poizvedbami, da bo vedenje transakcij pregledno in pod nadzorom?

## Obravnavane možnosti

* Neposredne parametrizirane SQL-poizvedbe prek MySQL Connector/Python, zbrane v repozitorijskih modulih
* ORM SQLAlchemy (oz. Flask-SQLAlchemy)
* Lepljenje vrednosti v SQL nize

## Izid odločitve

Izbrana možnost: »Neposredne parametrizirane SQL-poizvedbe«, ker zaklepanje (`FOR UPDATE`) in pogojna posodobitev pri prevzemu prijave ostaneta zapisana dobesedno in ju je mogoče pregledati ter testirati na pravi bazi. Pri ORM bi bilo enako vedenje skrito za abstrakcijo, ki jo je treba dodatno spoznati. Lepljenje vrednosti v SQL je izločeno, ker omogoča vrivanje SQL. Poizvedbe so zbrane v `repositories/`, zato poti in predloge ne vsebujejo SQL.

### Posledice

* Dobro, ker je vsaka poizvedba vidna v kodi in jo je mogoče preveriti neposredno v MySQL Workbench.
* Dobro, ker parametri (`%s`) preprečujejo vrivanje SQL, ne da bi bila potrebna dodatna knjižnica.
* Dobro, ker je manj odvisnosti in manj abstrakcije med kodo in bazo.
* Slabo, ker je treba preslikavo vrstic v objekte in ponavljajoče se poizvedbe CRUD pisati ročno.
* Slabo, ker ni samodejnih migracij; spremembe sheme se vodijo kot oštevilčene SQL-skripte (`sql/001-schema.sql`, …).
* Slabo, ker je koda vezana na narečje MySQL, zato bi zamenjava baze zahtevala pregled poizvedb.
