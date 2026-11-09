"""Poslovna pravila rezervacij (US-02, US-03).

Časi so v Pythonu in v bazi vedno v UTC (glej app/cas.py).

Ključno pravilo (ADR-0006): rezervacija se ustvari v transakciji, ki najprej
zaklene zapis opreme (SELECT ... FOR UPDATE). Dve sočasni zahtevi za isto
opremo se zato izvedeta ena za drugo: druga počaka, da prva potrdi, in nato
že vidi novo rezervacijo kot prekrivanje.
"""

from ..cas import zdaj_utc
from ..db import transakcija
from ..napake import PoslovnaNapaka
from ..repositories import oprema as repo_oprema
from ..repositories import rezervacije as repo_rezervacije


def preveri_termin(zacetek, konec, zdaj=None):
    """Začetek mora biti v prihodnosti in pred koncem (vsi časi v UTC)."""
    if zacetek is None or konec is None:
        raise PoslovnaNapaka("Vnesi začetek in konec rezervacije.")
    if zacetek >= konec:
        raise PoslovnaNapaka("Začetek mora biti pred koncem rezervacije.")
    if zacetek <= (zdaj or zdaj_utc()):
        raise PoslovnaNapaka("Začetek rezervacije mora biti v prihodnosti.")


def preveri_razpolozljivost(id_opreme, zacetek, konec):
    """Informativno preverjanje termina (US-02). Rezervacije NE ustvari.

    Vrne slovar: prosta (bool), razlog (besedilo ali None),
    prekrivajoce (seznam rezervacij). Ob neveljavnem terminu sproži
    PoslovnaNapaka.
    """
    preveri_termin(zacetek, konec)
    with transakcija() as k:
        oprema = repo_oprema.najdi(k, id_opreme)
        if oprema is None:
            raise PoslovnaNapaka("Izbrana oprema ne obstaja.")
        if oprema["stanje"] != "uporabna":
            return {"prosta": False, "prekrivajoce": [],
                    "razlog": "Oprema je nedelujoča in je ni mogoče rezervirati."}
        prekrivajoce = repo_rezervacije.prekrivajoce(k, id_opreme, zacetek, konec, zakleni=False)

    if prekrivajoce:
        return {"prosta": False, "prekrivajoce": prekrivajoce,
                "razlog": "Oprema je v izbranem terminu že rezervirana."}
    return {"prosta": True, "prekrivajoce": [], "razlog": None}


def ustvari(uporabnik, id_opreme, zacetek, konec):
    """Ustvari rezervacijo za prijavljenega uporabnika (US-03). Vrne njen id.

    Če katero pravilo ni izpolnjeno, sproži PoslovnaNapaka z razlogom
    zavrnitve; transakcija se razveljavi in v bazi ne ostane nič.
    """
    preveri_termin(zacetek, konec)

    with transakcija() as k:
        # 1. Zakleni opremo: druge rezervacije te opreme počakajo do konca transakcije.
        oprema = repo_oprema.zakleni(k, id_opreme)
        if oprema is None:
            raise PoslovnaNapaka("Izbrana oprema ne obstaja.")

        # 2. Stanje je prebrano pod zaklepom, zato je aktualno.
        if oprema["stanje"] != "uporabna":
            raise PoslovnaNapaka("Oprema je nedelujoča in je ni mogoče rezervirati.")

        # 3. Ponovno preveri prekrivanje: termin je medtem lahko zasedel nekdo drug.
        if repo_rezervacije.prekrivajoce(k, id_opreme, zacetek, konec):
            raise PoslovnaNapaka("Termin je že zaseden. Izberi drug termin.")

        # 4. Shrani. Transakcija se potrdi ob izhodu iz bloka with.
        return repo_rezervacije.ustvari(k, uporabnik.id, id_opreme, zacetek, konec)
