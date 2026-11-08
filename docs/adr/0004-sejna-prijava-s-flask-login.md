---
status: sprejeta
date: 2026-10-23
---

# Sejna prijava s Flask-Login

## Kontekst in opis problema

Aplikacijo uporabljajo zaposleni prek brskalnika. Zaledje mora pri vsaki zahtevi vedeti, kdo je prijavljen in s katero vlogo. Deaktivacija računa ali sprememba vloge mora učinkovati že ob naslednji zahtevi, tudi pri že prijavljenem uporabniku. Gesla morajo biti shranjena varno.


## Obravnavane možnosti

* Sejna prijava s Flask-Login (podpisan sejni piškotek) in zgoščevanje gesel z Werkzeug
* Prijava prek zunanjega ponudnika (npr. šolski Microsoft/Google račun, OAuth/OIDC)
* Lastna implementacija upravljanja sej

## Izid odločitve

Izbrana možnost: »Sejna prijava s Flask-Login«, ker se aplikacija uporablja samo prek brskalnika s strežniško sestavljenimi stranmi ([ADR-0003](0003-strezniski-html-z-jinja-predlogami.md)). Sejni piškotek je zato naraven in preprost mehanizem. JWT je smiseln pri API in ločenih odjemalcih, ki jih nimamo, poleg tega otežuje takojšen preklic dostopa. Prijava prek zunanjega ponudnika bi zahtevala registracijo aplikacije in sodelovanje šolskega skrbnika identitet, zato jo puščamo za kasnejšo nadgradnjo. Lastna implementacija sej bi po nepotrebnem povečala varnostno tveganje. V seji hranimo samo identifikator uporabnika, uporabnika pa ob vsaki zahtevi ponovno naložimo iz baze.

### Posledice

* Dobro, ker se deaktivacija računa ali sprememba vloge upošteva že pri naslednji zaščiteni zahtevi.
* Dobro, ker se gesla hranijo samo kot zgoščene vrednosti (`generate_password_hash`), geslo pa se nikoli ne shrani v sejo.
* Dobro, ker se Flask-Login neposredno povezuje s Flask-WTF in zaščito CSRF obrazcev.
* Slabo, ker je vsaka zaščitena zahteva dodatno branje iz baze.
* Slabo, ker je varnost sej odvisna od skrivnega `SECRET_KEY`, ki ga je treba hraniti zunaj repozitorija.
* Slabo, ker uporabniki potrebujejo še eno geslo, dokler ni uvedena prijava s šolskim računom.
