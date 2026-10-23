---
status: sprejeta
date: 2026-10-23
---

# Brez javne registracije – račune ustvarja administrator

## Kontekst in opis problema

Aplikacija je namenjena samo zaposlenim ene šole. Vloga uporabnika (učitelj, IKT skrbnik ali administrator) določa, katere operacije sme izvajati. Če bi si uporabnik sam ustvaril račun ali izbral vlogo, bi lahko do evidenc šolske opreme in prijav dostopale osebe, ki niso zaposlene na šoli.

Kako zagotoviti, da imajo dostop samo upravičene osebe s pravilno vlogo?

## Obravnavane možnosti

* Brez javne registracije: prvega administratorja ustvari lokalni ukaz, nadaljnje račune pa administrator v aplikaciji
* Javna registracija z naknadno odobritvijo administratorja
* Javna registracija, omejena na šolsko e-poštno domeno, s potrditvijo po e-pošti

## Izid odločitve

Izbrana možnost: »Brez javne registracije«, ker je krog uporabnikov majhen in znan vnaprej. Administrator ob ustvarjanju računa takoj določi pravilno vlogo, zato ni stanja »registriran, a neodobren«. Registracija z odobritvijo bi dodala obrazec, čakalno vrsto in stanja računa, ki ne prinašajo vrednosti. Omejitev na domeno bi zahtevala pošiljanje e-pošte, ki v MVP ni predvideno, in bi še vedno pomenila samodejno določanje vloge.

### Posledice

* Dobro, ker je površina za napad manjša: ni javnega obrazca za ustvarjanje računov, ki bi ga bilo mogoče zlorabiti.
* Dobro, ker ima vsak račun od začetka pravilno vlogo, ki jo je določil administrator.
* Dobro, ker je MVP preprostejši (brez potrjevanja e-pošte in čakalne vrste odobritev).
* Slabo, ker mora administrator ročno ustvariti vsak račun in posredovati začetno geslo.
* Slabo, ker samodejna ponastavitev gesla po e-pošti ni del MVP; pozabljeno geslo ponastavi administrator.
* Slabo, ker je potreben ločen lokalni ukaz (`flask --app app create-admin`) za prvega administratorja.
