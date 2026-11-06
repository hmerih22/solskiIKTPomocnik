"""Poslovna pravila rezervacij (F02, F03, F04, F08).

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
from ..repositories import uporabniki as repo_uporabniki
from . import obvestila


def preveri_termin(zacetek, konec, zdaj=None):
    """Termin mora biti v prihodnosti in začetek pred koncem (časi v UTC)."""
    zdaj = zdaj or zdaj_utc()
    if zacetek >= konec:
        raise PoslovnaNapaka("Začetek mora biti pred koncem rezervacije.")
    if zacetek <= zdaj:
        raise PoslovnaNapaka("Začetek rezervacije mora biti v prihodnosti.")


def preveri_razpolozljivost(id_opreme, zacetek, konec):
    """Informativno preverjanje (US-02); ne ustvari rezervacije.

    Vrne slovar: prosta (bool), razlog (besedilo ali None), prekrivajoce (seznam).
    Ob neveljavnem terminu sproži PoslovnaNapaka.
    """
    preveri_termin(zacetek, konec)
    with transakcija() as k:
        oprema = repo_oprema.najdi(k, id_opreme)
        if oprema is None:
            raise PoslovnaNapaka("Izbrana oprema ne obstaja.")
        if oprema["stanje"] != "uporabna":
            return {"prosta": False, "razlog": "Oprema je nedelujoča in je ni mogoče rezervirati.",
                    "prekrivajoce": []}
        prekrivajoce = repo_rezervacije.prekrivajoce(k, id_opreme, zacetek, konec, zakleni=False)

    if prekrivajoce:
        return {"prosta": False, "razlog": "Oprema je v izbranem terminu že rezervirana.",
                "prekrivajoce": prekrivajoce}
    return {"prosta": True, "razlog": None, "prekrivajoce": []}


def ustvari(uporabnik, id_opreme, zacetek, konec):
    """Ustvari rezervacijo za prijavljenega uporabnika (US-03). Vrne njen id."""
    preveri_termin(zacetek, konec)

    with transakcija() as k:
        # 1. Zakleni opremo – vse ostale rezervacije te opreme počakajo.
        oprema = repo_oprema.zakleni(k, id_opreme)
        if oprema is None:
            raise PoslovnaNapaka("Izbrana oprema ne obstaja.")

        # 2. Preveri uporabnost (stanje je prebrano pod zaklepom, zato je aktualno).
        if oprema["stanje"] != "uporabna":
            raise PoslovnaNapaka("Oprema je nedelujoča in je ni mogoče rezervirati.")

        # 3. Ponovno preveri prekrivanje – medtem je termin lahko zasedel nekdo drug.
        if repo_rezervacije.prekrivajoce(k, id_opreme, zacetek, konec):
            raise PoslovnaNapaka(
                "Termin je medtem zasedel drug uporabnik. Izberi drug termin."
            )

        # 4. Shrani. Transakcija se potrdi ob izhodu iz bloka with.
        id_rezervacije = repo_rezervacije.ustvari(k, uporabnik.id, id_opreme, zacetek, konec)
        rezervacija = repo_rezervacije.najdi(k, id_rezervacije)

    obvestila.nova_rezervacija(rezervacija, uporabnik.email)
    return id_rezervacije


def lahko_preklice(uporabnik, rezervacija):
    """Ali sme uporabnik preklicati rezervacijo (za prikaz gumba v predlogi)."""
    if rezervacija["status"] != "aktivna" or rezervacija["zacetek"] <= zdaj_utc():
        return False
    if rezervacija["uporabnik_id"] == uporabnik.id or uporabnik.je_administrator:
        return True
    return uporabnik.je_skrbnik and rezervacija["oprema_stanje"] == "nedelujoca"


def preklici(uporabnik, id_rezervacije, razlog=None):
    """Prekliče prihodnjo aktivno rezervacijo (US-04).

    - lastnik: lastno rezervacijo, razlog ni obvezen;
    - IKT skrbnik: tujo rezervacijo nedelujoče opreme, razlog je obvezen;
    - administrator: katerokoli tujo rezervacijo, razlog je obvezen.
    """
    razlog = (razlog or "").strip() or None

    with transakcija() as k:
        rezervacija = repo_rezervacije.zakleni(k, id_rezervacije)
        if rezervacija is None:
            raise PoslovnaNapaka("Rezervacija ne obstaja.")

        lastnik = rezervacija["uporabnik_id"] == uporabnik.id
        if not lastnik:
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
        posodobljena = repo_rezervacije.najdi(k, id_rezervacije)
        lastnik_rez = repo_uporabniki.najdi(k, rezervacija["uporabnik_id"])

    obvestila.preklicana_rezervacija(posodobljena, lastnik_rez["email"])


# --- Nadgradnja F08: prevzem in vračilo -------------------------------------

def zabelezi_prevzem(uporabnik, id_rezervacije):
    if not uporabnik.je_skrbnik:
        raise Prepovedano()

    with transakcija() as k:
        rezervacija = repo_rezervacije.najdi(k, id_rezervacije)
        if rezervacija is None:
            raise PoslovnaNapaka("Rezervacija ne obstaja.")
        # Enak vrstni red zaklepanja kot pri ustvarjanju: najprej oprema.
        oprema = repo_oprema.zakleni(k, rezervacija["oprema_id"])
        rezervacija = repo_rezervacije.zakleni(k, id_rezervacije)

        if rezervacija["status"] != "aktivna":
            raise PoslovnaNapaka("Preklicane rezervacije ni mogoče označiti kot prevzete.")
        if oprema["stanje"] != "uporabna":
            raise PoslovnaNapaka("Nedelujoče opreme ni mogoče izdati.")
        if rezervacija["prevzeta_ob"] is not None:
            raise PoslovnaNapaka("Prevzem te rezervacije je že zabeležen.")
        if repo_rezervacije.izposojena_pri_drugi(k, rezervacija["oprema_id"], id_rezervacije):
            raise PoslovnaNapaka("Oprema je še izposojena pri drugi rezervaciji in ni vrnjena.")

        repo_rezervacije.zabelezi_prevzem(k, id_rezervacije, zdaj_utc())


def zabelezi_vracilo(uporabnik, id_rezervacije):
    if not uporabnik.je_skrbnik:
        raise Prepovedano()

    with transakcija() as k:
        rezervacija = repo_rezervacije.zakleni(k, id_rezervacije)
        if rezervacija is None:
            raise PoslovnaNapaka("Rezervacija ne obstaja.")
        if rezervacija["prevzeta_ob"] is None:
            raise PoslovnaNapaka("Vračilo je mogoče zabeležiti šele po prevzemu.")
        if rezervacija["vrnjena_ob"] is not None:
            raise PoslovnaNapaka("Vračilo te rezervacije je že zabeleženo.")

        repo_rezervacije.zabelezi_vracilo(k, id_rezervacije, zdaj_utc())
