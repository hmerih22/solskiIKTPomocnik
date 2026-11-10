"""Poslovna pravila rezervacij (US-02, US-03, US-04).

Časi so v Pythonu in v bazi vedno v UTC (glej app/cas.py).

Ključno pravilo (ADR-0006): rezervacija se ustvari v transakciji, ki najprej
zaklene zapis opreme (SELECT ... FOR UPDATE). Dve sočasni zahtevi za isto
opremo se zato izvedeta ena za drugo: druga počaka, da prva potrdi, in nato
že vidi novo rezervacijo kot prekrivanje.
"""

from ..cas import zdaj_utc
from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
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


def lahko_preklice(uporabnik, rezervacija):
    """Ali sme uporabnik preklicati rezervacijo (za prikaz gumba v predlogi).

    Preklicati je mogoče samo aktivno rezervacijo, ki se še ni začela.
    """
    if rezervacija["status"] != "aktivna" or rezervacija["zacetek"] <= zdaj_utc():
        return False
    if rezervacija["uporabnik_id"] == uporabnik.id or uporabnik.je_administrator:
        return True
    return uporabnik.je_skrbnik and rezervacija["oprema_stanje"] == "nedelujoca"


def preklici(uporabnik, id_rezervacije, razlog=None):
    """Prekliče prihodnjo aktivno rezervacijo (US-04).

    - lastnik: lastno rezervacijo, razlog ni obvezen;
    - IKT skrbnik: tujo rezervacijo NEDELUJOČE opreme, razlog je obvezen;
    - administrator: katerokoli tujo rezervacijo, razlog je obvezen.

    Shrani se status 'preklicana', čas preklica in kdo jo je preklical.
    Preklicana rezervacija ne zaseda več termina.
    """
    razlog = (razlog or "").strip() or None

    with transakcija() as k:
        rezervacija = repo_rezervacije.zakleni(k, id_rezervacije)
        if rezervacija is None:
            raise PoslovnaNapaka("Rezervacija ne obstaja.")
        if rezervacija["uporabnik_id"] != uporabnik.id:
            if uporabnik.je_administrator:
                pass
            elif uporabnik.je_skrbnik:
                oprema = repo_oprema.najdi(k, rezervacija["oprema_id"])
                if oprema["stanje"] != "nedelujoca":
                    raise Prepovedano()
            else:
                raise Prepovedano()
            if not razlog:
                raise PoslovnaNapaka("Pri preklicu tuje rezervacije je razlog obvezen.")
        if rezervacija["status"] != "aktivna":
            raise PoslovnaNapaka("Rezervacija je že preklicana.")
        if rezervacija["zacetek"] <= zdaj_utc():
            raise PoslovnaNapaka("Rezervacije, ki se je že začela, ni mogoče preklicati.")

        repo_rezervacije.preklici(k, id_rezervacije, uporabnik.id, razlog, zdaj_utc())
