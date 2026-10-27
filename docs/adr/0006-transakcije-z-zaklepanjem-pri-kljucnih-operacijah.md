---
status: sprejeta
date: 2026-10-23
---

# Transakcije z zaklepanjem pri ključnih operacijah

## Kontekst in opis problema

Dva učitelja lahko hkrati oddata rezervacijo istega projektorja za prekrivajoča se termina. Dva IKT skrbnika lahko hkrati prevzameta isto novo prijavo. Če aplikacija najprej prebere stanje in šele nato zapiše spremembo, lahko obe zahtevi preverjanje uspešno prestaneta, kar povzroči dvojno rezervacijo ali dvojni prevzem. Enolični ključ na (oprema, začetek) ne prepreči vseh prekrivanj, saj se lahko termina z različnim začetkom vseeno prekrivata (npr. 9.00–10.00 in 9.30–10.30).

## Obravnavane možnosti

* Transakcija z zaklepanjem zapisa opreme (`SELECT ... FOR UPDATE`) pred preverjanjem in zapisom; pogojna posodobitev pri prevzemu prijave
* Preverjanje samo v aplikaciji brez transakcij (najprej preberi, nato zapiši)
* Enolični ključ na (oprema, začetni čas)

## Izid odločitve

Izbrana možnost: »Transakcija z zaklepanjem zapisa opreme in pogojna posodobitev pri prevzemu prijave«, ker zaklep zapisa opreme serializira vse zahteve za isto opremo. Preverjanje prekrivanja in zapis rezervacije se zato izvedeta kot nedeljiva celota, zahteve za drugo opremo pa tečejo vzporedno. Prevzem prijave se izvede s pogojno posodobitvijo `... WHERE status = 'nova'`; zaledje preveri število spremenjenih vrstic in drugemu skrbniku sporoči, da je prijava že prevzeta. Preverjanje brez transakcije ima opisano tekmovalno stanje. Enolični ključ ne zajame prekrivanj z različnim začetkom. Optimistično zaklepanje bi zahtevalo logiko ponovnih poskusov. 

### Posledice

* Dobro, ker sočasni zahtevi ne moreta ustvariti dveh aktivnih prekrivajočih se rezervacij iste opreme (US-03) ali dveh prevzemov iste prijave (US-06).
* Dobro, ker isti zaklep zapisa opreme uskladi tudi spremembo uporabnosti opreme, zato rezervacija ne more uspeti v trenutku, ko je oprema označena kot nedelujoča (US-07).
* Dobro, ker se ob napaki nepotrjena transakcija razveljavi in ne ostanejo delni zapisi.
* Slabo, ker morajo vsi postopki, ki ustvarjajo rezervacije, uporabljati enak vrstni red zaklepanja; odstopanje bi ponovno odprlo tekmovalno stanje ali povzročilo zastoj (deadlock).
* Slabo, ker zahteve za isto opremo čakajo druga na drugo; pri obsegu ene šole je to zanemarljivo, pri večjem obsegu bi lahko postalo ozko grlo.
* Slabo, ker je pravilnost težje preveriti; potrebni so testi sočasnih zahtev na pravi MySQL bazi, ne le enotski testi.
