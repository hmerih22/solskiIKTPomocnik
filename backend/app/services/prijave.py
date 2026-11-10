"""Poslovna pravila prijav težav (US-05, US-06).

Stanja prijave: nova → v_obravnavi → resena. Drugih prehodov ni.
Prevzem je pogojna posodobitev (... WHERE status = 'nova'), zato ga dva
skrbnika ne moreta hkrati uspešno izvesti (ADR-0006).
"""

from ..cas import zdaj_utc
from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import oprema as repo_oprema
from ..repositories import prijave as repo_prijave
from ..repositories import ucilnice as repo_ucilnice
from ..repositories import uporabniki as repo_uporabniki

STATUSI = {"nova": "Nova", "v_obravnavi": "V obravnavi", "resena": "Rešena"}


def lahko_vidi(uporabnik, prijava):
    """Prijavo vidijo prijavitelj, IKT skrbniki in administratorji (US-05, US-06)."""
    return prijava["prijavitelj_id"] == uporabnik.id or uporabnik.je_skrbnik


def lahko_zakljuci(uporabnik, prijava):
    """Prijavo v obravnavi zaključi odgovorni skrbnik ali administrator."""
    if prijava["status"] != "v_obravnavi":
        return False
    return prijava["skrbnik_id"] == uporabnik.id or uporabnik.je_administrator


def oddaj(uporabnik, id_opreme, id_ucilnice, naslov, opis):
    """Odda novo prijavo težave (US-05). Vrne id prijave.

    Prijava mora biti povezana z opremo, učilnico ali obema.
    """
    id_opreme = id_opreme or None
    id_ucilnice = id_ucilnice or None
    naslov = (naslov or "").strip()
    opis = (opis or "").strip()
    if id_opreme is None and id_ucilnice is None:
        raise PoslovnaNapaka("Izberi opremo, učilnico ali oboje.")
    if not naslov or not opis:
        raise PoslovnaNapaka("Naslov in opis sta obvezna.")

    with transakcija() as k:
        if id_opreme is not None and repo_oprema.najdi(k, id_opreme) is None:
            raise PoslovnaNapaka("Izbrana oprema ne obstaja.")
        if id_ucilnice is not None and repo_ucilnice.najdi(k, id_ucilnice) is None:
            raise PoslovnaNapaka("Izbrana učilnica ne obstaja.")
        return repo_prijave.ustvari(k, uporabnik.id, id_opreme, id_ucilnice, naslov, opis)


# --- Obravnava (US-06) ----------------------------------------------------------

def prevzemi(uporabnik, id_prijave):
    """IKT skrbnik ali administrator prevzame novo prijavo in postane zanjo odgovoren."""
    if not uporabnik.je_skrbnik:
        raise Prepovedano()

    with transakcija() as k:
        spremenjenih = repo_prijave.prevzemi(k, id_prijave, uporabnik.id, zdaj_utc())
        if spremenjenih == 0:
            # Nič se ni spremenilo: prijava ne obstaja ali ni več 'nova'.
            if repo_prijave.najdi(k, id_prijave) is None:
                raise PoslovnaNapaka("Prijava ne obstaja.")
            raise PoslovnaNapaka("Prijavo je že prevzel drug skrbnik.")


def zakljuci(uporabnik, id_prijave, resitev):
    """Odgovorni skrbnik ali administrator zaključi prijavo v obravnavi z rešitvijo.

    Zaključek ne spremeni stanja opreme: to skrbnik naredi posebej (US-07).
    """
    if not uporabnik.je_skrbnik:
        raise Prepovedano()
    resitev = (resitev or "").strip()

    with transakcija() as k:
        prijava = repo_prijave.zakleni(k, id_prijave)
        if prijava is None:
            raise PoslovnaNapaka("Prijava ne obstaja.")
        if not lahko_zakljuci(uporabnik, prijava):
            if prijava["status"] != "v_obravnavi":
                raise PoslovnaNapaka("Zaključiti je mogoče samo prijavo v obravnavi.")
            raise Prepovedano()
        if not resitev:
            raise PoslovnaNapaka("Pred zaključkom vnesi opis rešitve.")

        repo_prijave.zakljuci(k, id_prijave, resitev, zdaj_utc())


def prerazporedi(uporabnik, id_prijave, id_novega_skrbnika):
    """Administrator dodeli prijavo v obravnavi drugemu skrbniku (US-06).

    Novi skrbnik mora biti aktiven IKT skrbnik ali administrator. Čas prvega
    prevzema ostane nespremenjen.
    """
    if not uporabnik.je_administrator:
        raise Prepovedano()

    with transakcija() as k:
        prijava = repo_prijave.zakleni(k, id_prijave)
        if prijava is None:
            raise PoslovnaNapaka("Prijava ne obstaja.")
        if prijava["status"] != "v_obravnavi":
            raise PoslovnaNapaka("Prerazporediti je mogoče samo prijavo v obravnavi.")

        # Zaklenemo novega skrbnika, da ga medtem nihče ne deaktivira.
        novi = repo_uporabniki.zakleni(k, id_novega_skrbnika) if id_novega_skrbnika else None
        if (novi is None or not novi["aktiven"]
                or novi["vloga"] not in ("ikt_skrbnik", "administrator")):
            raise PoslovnaNapaka(
                "Prijavo lahko dodeliš samo aktivnemu IKT skrbniku ali administratorju."
            )

        repo_prijave.prerazporedi(k, id_prijave, id_novega_skrbnika)
