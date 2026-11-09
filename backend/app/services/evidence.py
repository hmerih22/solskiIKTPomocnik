"""Osnovne evidence: učilnice in oprema (US-15).

Vse operacije lahko izvede samo administrator. Storitev to preveri sama,
zato pravilo velja tudi pri zahtevi, poslani mimo uporabniškega vmesnika.
Podatki se zapišejo v eni transakciji: ob napaki se ne shrani nič.
"""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError

from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import ucilnice as repo_ucilnice


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
