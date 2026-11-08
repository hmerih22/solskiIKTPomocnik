---
status: sprejeta
date: 2026-10-23
---

# Strežniško sestavljen HTML z Jinja predlogami

## Kontekst in opis problema

Uporabniški vmesnik je sestavljen predvsem iz seznamov (oprema, rezervacije, prijave) in obrazcev (rezervacija, prijava težave, urejanje računov). Ni zahtev po delu brez povezave ali po sprotnem osveževanju v realnem času. Odločiti je treba, ali naj HTML sestavlja strežnik ali ločena odjemalska aplikacija, ki komunicira prek API.


## Obravnavane možnosti

* Strežniško upodabljanje s Flask in Jinja predlogami (HTML, CSS, po potrebi malo JavaScripta)
* Ločena enostranska aplikacija (SPA, npr. React ali Vue) in REST API v Flasku

## Izid odločitve

Izbrana možnost: »Strežniško upodabljanje s Flask in Jinja predlogami«, ker obrazci in preglednice v celoti pokrijejo zahtevane poteke. Podatki in prikaz ostanejo v enem projektu, zato ni treba vzdrževati API pogodbe in je ni treba ločeno avtenticirati. SPA bi podvojila delo: definicijo API, odjemalsko usmerjanje, upravljanje stanja in dodatno zaščito. Za seznam opreme in obrazec za rezervacijo tega ne potrebujemo. Knjižnico htmx lahko dodamo pozneje, če se pokaže potreba po delnih posodobitvah, ne da bi spreminjali osnovni pristop.

### Posledice

* Dobro, ker osnovni poteki delujejo z običajnimi obrazci tudi brez JavaScripta, kar izboljša zanesljivost in dostopnost.
* Dobro, ker Jinja samodejno ubeži uporabniška besedila (npr. opise težav), kar zmanjša tveganje za XSS.
* Dobro, ker se zaščita pred CSRF in sejna prijava uporabita neposredno, brez ločene avtentikacije API.
* Slabo, ker vsaka akcija povzroči ponovno nalaganje strani, kar je manj tekoče kot pri SPA.
* Slabo, ker ni javnega API; morebitna mobilna aplikacija ali integracija bi ga zahtevala naknadno.
* Slabo, ker je direktorij `frontend/` vezan na zaledje (predloge uporablja Flask) in ga ni mogoče objaviti samostojno.
