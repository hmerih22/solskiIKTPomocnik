"""Poslovna pravila opreme in osnovnih evidenc (F07, US-15)."""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError

from ..cas import zdaj_utc
from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import oprema as repo_oprema
from ..repositories import rezervacije as repo_rezervacije
from ..repositories import ucilnice as repo_ucilnice

STANJA = ("uporabna", "nedelujoca")


def spremeni_stanje(uporabnik, id_opreme, stanje):
    """IKT skrbnik ali administrator označi opremo kot uporabno/nedelujočo (US-07).

    Zapis opreme se zaklene enako kot pri ustvarjanju rezervacije, zato
    rezervacija ne more uspeti v trenutku, ko je oprema označena kot nedelujoča.
    Vrne število prihodnjih aktivnih rezervacij (za opozorilo skrbniku).
    """
    if not uporabnik.je_skrbnik:
        raise Prepovedano()
    if stanje not in STANJA:
        raise PoslovnaNapaka("Neveljavno stanje opreme.")

    with transakcija() as k:
        if repo_oprema.zakleni(k, id_opreme) is None:
            raise PoslovnaNapaka("Oprema ne obstaja.")
        repo_oprema.nastavi_stanje(k, id_opreme, stanje)
        prihodnje = repo_rezervacije.zasedeni_termini(k, id_opreme, zdaj_utc())
    return len(prihodnje)


def _je_podvojena_vrednost(napaka):
    return isinstance(napaka, IntegrityError) and napaka.errno == errorcode.ER_DUP_ENTRY


# --- Učilnice (administrator) ------------------------------------------------

def shrani_ucilnico(uporabnik, id_ucilnice, oznaka, naziv, opis):
    """Doda (id_ucilnice=None) ali uredi učilnico. Vrne njen id."""
    if not uporabnik.je_administrator:
        raise Prepovedano()

    try:
        with transakcija() as k:
            obstojeca = repo_ucilnice.najdi_po_oznaki(k, oznaka)
            if obstojeca and obstojeca["id"] != id_ucilnice:
                raise PoslovnaNapaka(f"Učilnica z oznako »{oznaka}« že obstaja.")
            if id_ucilnice is None:
                return repo_ucilnice.ustvari(k, oznaka, naziv, opis)
            if repo_ucilnice.najdi(k, id_ucilnice) is None:
                raise PoslovnaNapaka("Učilnica ne obstaja.")
            repo_ucilnice.posodobi(k, id_ucilnice, oznaka, naziv, opis)
            return id_ucilnice
    except IntegrityError as e:
        # Če je dve enaki oznaki hkrati vnesel nekdo drug, napako sproži baza.
        if _je_podvojena_vrednost(e):
            raise PoslovnaNapaka(f"Učilnica z oznako »{oznaka}« že obstaja.") from e
        raise


# --- Oprema (administrator) --------------------------------------------------

def shrani_opremo(uporabnik, id_opreme, naziv, inventarna_stevilka, vrsta, opis, stanje,
                  id_ucilnice):
    """Doda (id_opreme=None) ali uredi opremo. Vrne njen id."""
    if not uporabnik.je_administrator:
        raise Prepovedano()
    if stanje not in STANJA:
        raise PoslovnaNapaka("Neveljavno stanje opreme.")

    try:
        with transakcija() as k:
            if repo_ucilnice.najdi(k, id_ucilnice) is None:
                raise PoslovnaNapaka("Izbrana učilnica ne obstaja.")
            obstojeca = repo_oprema.najdi_po_inventarni(k, inventarna_stevilka)
            if obstojeca and obstojeca["id"] != id_opreme:
                raise PoslovnaNapaka(
                    f"Oprema z inventarno številko »{inventarna_stevilka}« že obstaja."
                )
            if id_opreme is None:
                return repo_oprema.ustvari(k, naziv, inventarna_stevilka, vrsta, opis, stanje,
                                           id_ucilnice)

            if repo_oprema.zakleni(k, id_opreme) is None:
                raise PoslovnaNapaka("Oprema ne obstaja.")
            repo_oprema.posodobi(k, id_opreme, naziv, inventarna_stevilka, vrsta, opis, id_ucilnice)
            repo_oprema.nastavi_stanje(k, id_opreme, stanje)
            return id_opreme
    except IntegrityError as e:
        if _je_podvojena_vrednost(e):
            raise PoslovnaNapaka(
                f"Oprema z inventarno številko »{inventarna_stevilka}« že obstaja."
            ) from e
        raise
