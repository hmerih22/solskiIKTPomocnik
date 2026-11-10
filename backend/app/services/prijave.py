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

STATUSI = {"nova": "Nova", "v_obravnavi": "V obravnavi", "resena": "Rešena"}


def lahko_vidi(uporabnik, prijava):
    """Prijavo vidijo prijavitelj, IKT skrbniki in administratorji (US-05, US-06)."""
    return prijava["prijavitelj_id"] == uporabnik.id or uporabnik.je_skrbnik


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
