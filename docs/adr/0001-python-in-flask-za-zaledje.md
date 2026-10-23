---
status: sprejeta
date: 2026-10-23
---

# Python in Flask za zaledje

## Kontekst in opis problema

Aplikacija mora obdelovati zahteve iz brskalnika, preverjati pravice treh vlog in izvajati poslovna pravila: rezervacije brez prekrivanja, blokado nedelujoče opreme ter prevzem in zaključek prijav. Projekt razvija en razvijalec v omejenem času, zato mora biti ogrodje dovolj preprosto za hiter začetek, hkrati pa mora pustiti poslovna pravila jasno vidna v lastni kodi, ne skrita v samodejnem delovanju ogrodja.

Katero ogrodje za zaledje omogoča pregleden zapis poslovnih pravil pri majhni ekipi in omejenem obsegu?

## Obravnavane možnosti

* Python in Flask
* Python in Django
* Node.js in Express
* Java in Spring Boot

## Izid odločitve

Izbrana možnost: »Python in Flask«, ker je mikroogrodje z majhnim jedrom. Usmerjanje zahtev, obrazce in prijavo dodamo z izbranimi razširitvami, pravila rezervacij in prijav pa ostanejo zapisana v lastnih modulih, kjer jih je mogoče brati in testirati. Django prinaša lasten ORM, administracijo in uporabniški model, ki bi za ta obseg vsilili več konvencij, kot jih potrebujemo. Spring Boot pomeni bistveno več nastavitev za enako funkcionalnost. Express bi zahteval JavaScript na zaledju, za katerega razvijalec nima prednosti pred Pythonom.

### Posledice

* Dobro, ker je obdelava zahteve (pot → preverjanje → poslovna logika → odgovor) eksplicitna in jo je lahko slediti ter razložiti.
* Dobro, ker Flask testni odjemalec in pytest omogočata preprosto testiranje poti in pravic brez zagona strežnika.
* Dobro, ker Python ponuja zrele knjižnice za vse potrebe projekta (MySQL, seje, obrazci, gesla).
* Slabo, ker Flask ne ponuja vgrajene administracije, uporabniškega modela ali migracij; te dele moramo izbrati in povezati sami.
* Slabo, ker je struktura projekta stvar dogovora; brez discipline se lahko poti, logika in SQL pomešajo (to naslavlja [ADR-0002](0002-enotna-aplikacija-z-locenimi-moduli.md)).
