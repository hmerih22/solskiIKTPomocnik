"""Osnovne evidence: učilnice in oprema (US-15).

Vse operacije lahko izvede samo administrator. Storitev to preveri sama,
zato pravilo velja tudi pri zahtevi, poslani mimo uporabniškega vmesnika.
Podatki se zapišejo v eni transakciji: ob napaki se ne shrani nič.
"""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError

from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..cas import zdaj_utc
from ..repositories import oprema as repo_oprema
from ..repositories import rezervacije as repo_rezervacije
from ..repositories import ucilnice as repo_ucilnice

STANJA = ("uporabna", "nedelujoca")


def _ocisti(vrednost):
    return (vrednost or "").strip()


def _je_podvojena_vrednost(napaka):
    return napaka.errno == errorcode.ER_DUP_ENTRY


def _preveri_administratorja(uporabnik):
    if not uporabnik.je_administrator:
        raise Prepovedano()


# --- Učilnice ----------------------------------------------------------------

def dodaj_ucilnico(uporabnik, oznaka, naziv, opis=None):
    """Doda učilnico z enolično oznako. Vrne njen id."""
    _preveri_administratorja(uporabnik)
    oznaka, naziv, opis = _ocisti(oznaka), _ocisti(naziv), _ocisti(opis) or None
    if not oznaka or not naziv:
        raise PoslovnaNapaka("Oznaka in naziv učilnice sta obvezna.")

    napaka = PoslovnaNapaka(f"Učilnica z oznako »{oznaka}« že obstaja.")
    try:
        with transakcija() as k:
            if repo_ucilnice.najdi_po_oznaki(k, oznaka):
                raise napaka
            return repo_ucilnice.ustvari(k, oznaka, naziv, opis)
    except IntegrityError as e:
        # Dva sočasna vnosa iste oznake: drugega zavrne omejitev UNIQUE.
        if _je_podvojena_vrednost(e):
            raise napaka from e
        raise


def uredi_ucilnico(uporabnik, id_ucilnice, naziv, opis=None):
    """Spremeni naziv in opis. Oznaka se po vnosu ne spreminja."""
    _preveri_administratorja(uporabnik)
    naziv, opis = _ocisti(naziv), _ocisti(opis) or None
    if not naziv:
        raise PoslovnaNapaka("Naziv učilnice je obvezen.")

    with transakcija() as k:
        if repo_ucilnice.najdi(k, id_ucilnice) is None:
            raise PoslovnaNapaka("Učilnica ne obstaja.")
        repo_ucilnice.posodobi(k, id_ucilnice, naziv, opis)


# --- Oprema ------------------------------------------------------------------

def shrani_opremo(uporabnik, id_opreme, naziv, inventarna_stevilka, vrsta, opis, stanje,
                  ucilnica_id):
    """Doda (id_opreme=None) ali uredi opremo. Vrne njen id."""
    _preveri_administratorja(uporabnik)
    naziv, inventarna_stevilka, vrsta = _ocisti(naziv), _ocisti(inventarna_stevilka), _ocisti(vrsta)
    opis = _ocisti(opis) or None
    if not naziv or not inventarna_stevilka or not vrsta:
        raise PoslovnaNapaka("Naziv, inventarna številka in vrsta so obvezni.")
    if stanje not in STANJA:
        raise PoslovnaNapaka("Neveljavno stanje opreme.")

    napaka = PoslovnaNapaka(f"Oprema z inventarno številko »{inventarna_stevilka}« že obstaja.")
    try:
        with transakcija() as k:
            if repo_ucilnice.najdi(k, ucilnica_id) is None:
                raise PoslovnaNapaka("Izbrana učilnica ne obstaja.")
            obstojeca = repo_oprema.najdi_po_inventarni(k, inventarna_stevilka)
            if obstojeca and obstojeca["id"] != id_opreme:
                raise napaka

            if id_opreme is None:
                return repo_oprema.ustvari(k, naziv, inventarna_stevilka, vrsta, opis, stanje,
                                           ucilnica_id)
            # Zaklep: med urejanjem ne more nastati rezervacija z zastarelim stanjem.
            if repo_oprema.zakleni(k, id_opreme) is None:
                raise PoslovnaNapaka("Oprema ne obstaja.")
            repo_oprema.posodobi(k, id_opreme, naziv, inventarna_stevilka, vrsta, opis, stanje,
                                 ucilnica_id)
            return id_opreme
    except IntegrityError as e:
        if _je_podvojena_vrednost(e):
            raise napaka from e
        raise


def spremeni_stanje_opreme(uporabnik, id_opreme, stanje):
    """IKT skrbnik ali administrator označi opremo kot uporabno ali nedelujočo (US-07).

    Zapis opreme se zaklene enako kot pri ustvarjanju rezervacije, zato
    rezervacija ne more uspeti v trenutku, ko je oprema označena kot nedelujoča.

    Obstoječe rezervacije se NE prekličejo samodejno. Funkcija vrne število
    prihodnjih in tekočih aktivnih rezervacij, da lahko skrbnik dobi opozorilo.
    """
    if not uporabnik.je_skrbnik:
        raise Prepovedano()
    if stanje not in STANJA:
        raise PoslovnaNapaka("Neveljavno stanje opreme.")

    with transakcija() as k:
        if repo_oprema.zakleni(k, id_opreme) is None:
            raise PoslovnaNapaka("Oprema ne obstaja.")
        repo_oprema.nastavi_stanje(k, id_opreme, stanje)
        return len(repo_rezervacije.zasedeni_termini(k, id_opreme, zdaj_utc()))
