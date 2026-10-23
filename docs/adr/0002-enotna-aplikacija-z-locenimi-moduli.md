---
status: sprejeta
date: 2026-10-23
---

# Enotna aplikacija z ločenimi moduli

## Kontekst in opis problema

Sistem pokriva več področij: prijavo, opremo, rezervacije, prijave težav in administracijo. Uporablja ga ena šola z nekaj deset sočasnimi uporabniki. Odločiti je treba, ali bodo ta področja ločene omrežne storitve ali deli ene aplikacije, ter kako preprečiti, da bi koda z rastjo postala nepregledna.

Kako razdeliti sistem, da bo pregleden, a ne bo nosil infrastrukturnih stroškov, ki jih obseg ene šole ne upravičuje?

## Obravnavane možnosti

* Enotna aplikacija (modularni monolit) z ločenimi moduli po področjih in plasteh
* Mikrostoritve (npr. ločeni storitvi za rezervacije in prijave)
* Enotna aplikacija brez notranje delitve (vse v nekaj datotekah)

## Izid odločitve

Izbrana možnost: »Enotna aplikacija z ločenimi moduli«, ker obseg ene šole ne potrebuje neodvisnega skaliranja ali ločenih objav posameznih delov. Ključne operacije, na primer ustvarjanje rezervacije ob preverjanju stanja opreme, morajo potekati v eni transakciji nad isto bazo. Pri mikrostoritvah bi to zahtevalo porazdeljeno usklajevanje. Aplikacija brez notranje delitve bi bila hitra za začetek, vendar bi se poti, pravila in SQL pomešali. Zato aplikacijo delimo na module po področjih (`auth`, `oprema`, `rezervacije`, `prijave`, `admin`) in po plasteh (poti → `services/` → `repositories/` → `db`).

### Posledice

* Dobro, ker se aplikacija zažene in objavi kot ena enota z enim procesom in eno bazo, kar poenostavi lokalni razvoj in testiranje.
* Dobro, ker se transakcije, ki zajemajo opremo, rezervacije in prijave, izvajajo lokalno v eni povezavi z bazo.
* Dobro, ker ločitev plasti omogoča testiranje poslovnih pravil neodvisno od predlog in poti.
* Dobro, ker je vzdrževanje preprosto: ena koda, ena baza in en postopek namestitve, brez omrežne komunikacije med storitvami.
* Slabo, ker se meje med moduli vzdržujejo z dogovorom, ne s tehnično ločitvijo; neposreden klic mimo plasti je mogoč.
* Slabo, ker bi poznejša razdelitev na storitve, če bi jo sistem kdaj potreboval, zahtevala preoblikovanje.
