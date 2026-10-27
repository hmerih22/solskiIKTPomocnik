---
status: sprejeta
date: 2026-10-23
---

# Python in Flask za zaledje

## Kontekst in opis problema

Aplikacija mora obdelovati zahteve iz brskalnika, preverjati pravice treh vlog in izvajati poslovna pravila: rezervacije brez prekrivanja, blokado nedelujoče opreme ter prevzem in zaključek prijav. Projekt razvija en razvijalec v omejenem času, zato mora biti ogrodje dovolj preprosto za hiter začetek, hkrati pa mora pustiti poslovna pravila jasno vidna v lastni kodi, ne skrita v samodejnem delovanju ogrodja.


## Obravnavane možnosti

* Python in Flask
* Python in Django

## Izid odločitve

Flask, ker omogoča preprosto strukturo, neposreden nadzor nad posameznimi deli aplikacije in dovolj funkcionalnosti za načrtovani obseg. Django ima več vgrajenih funkcij, vendar bi prinesel dodatno kompleksnost.

### Posledice

* Dobro, ker je obdelava zahteve (pot → preverjanje → poslovna logika → odgovor) eksplicitna in jo je lahko slediti ter razložiti.
* Dobro, ker Flask testni odjemalec in pytest omogočata preprosto testiranje poti in pravic brez zagona strežnika.
* Dobro, ker Python ponuja zrele knjižnice za vse potrebe projekta (MySQL, seje, obrazci, gesla).
* Slabo, ker Flask ne ponuja vgrajene administracije, uporabniškega modela ali migracij; te dele moramo izbrati in povezati sami.
* Slabo, ker je struktura projekta stvar dogovora; brez discipline se lahko poti, logika in SQL pomešajo.
