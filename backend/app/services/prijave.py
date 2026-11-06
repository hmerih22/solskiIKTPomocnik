"""Poslovna pravila prijav težav (F05, F06, F09, F10).

Stanja prijave: nova → v_obravnavi → resena. Drugih prehodov ni.
Prevzem je pogojna posodobitev (... WHERE status = 'nova'), zato ga
dva skrbnika ne moreta hkrati uspešno izvesti (ADR-0006).
"""

import secrets
from pathlib import Path

from flask import current_app

from ..cas import zdaj_utc
from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import oprema as repo_oprema
from ..repositories import prijave as repo_prijave
from ..repositories import ucilnice as repo_ucilnice
from ..repositories import uporabniki as repo_uporabniki
from . import obvestila

NAJVEC_PRIPONK = 3
NAJVECJA_VELIKOST = 5 * 1024 * 1024  # 5 MiB

# Vrsta datoteke se določi po prvih bajtih vsebine ("magic bytes"),
# ne po končnici, ki bi jo lahko kdo poljubno spremenil.
PODPISI = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"%PDF-", "application/pdf", ".pdf"),
]


# --- Pravice -----------------------------------------------------------------

def lahko_vidi(uporabnik, prijava):
    """Prijavo vidijo prijavitelj, IKT skrbniki in administratorji (US-05, US-06)."""
    return prijava["prijavitelj_id"] == uporabnik.id or uporabnik.je_skrbnik


def lahko_zakljuci(uporabnik, prijava):
    if prijava["status"] != "v_obravnavi":
        return False
    return prijava["skrbnik_id"] == uporabnik.id or uporabnik.je_administrator


def lahko_komentira(uporabnik, prijava):
    """Komentirajo prijavitelj, odgovorni skrbnik in administrator (US-09)."""
    if prijava["status"] == "resena":
        return False
    return (
        prijava["prijavitelj_id"] == uporabnik.id
        or prijava["skrbnik_id"] == uporabnik.id
        or uporabnik.je_administrator
    )


# --- Oddaja ------------------------------------------------------------------

def _preberi_priponke(datoteke):
    """Preveri priponke in vrne seznam (izvirno_ime, vrsta, koncnica, vsebina).

    Če katera ne ustreza pravilom, sproži PoslovnaNapaka, preden se karkoli shrani.
    """
    datoteke = [d for d in (datoteke or []) if d and d.filename]
    if len(datoteke) > NAJVEC_PRIPONK:
        raise PoslovnaNapaka(f"Priložiš lahko največ {NAJVEC_PRIPONK} datoteke.")

    rezultat = []
    for datoteka in datoteke:
        vsebina = datoteka.read(NAJVECJA_VELIKOST + 1)
        if len(vsebina) == 0:
            raise PoslovnaNapaka(f"Datoteka »{datoteka.filename}« je prazna.")
        if len(vsebina) > NAJVECJA_VELIKOST:
            raise PoslovnaNapaka(f"Datoteka »{datoteka.filename}« je večja od 5 MiB.")
        for podpis, vrsta, koncnica in PODPISI:
            if vsebina.startswith(podpis):
                break
        else:
            raise PoslovnaNapaka(
                f"Datoteka »{datoteka.filename}« ni JPEG, PNG ali PDF."
            )
        izvirno_ime = Path(datoteka.filename).name[:255]
        rezultat.append((izvirno_ime, vrsta, koncnica, vsebina))
    return rezultat


def mapa_priponk():
    mapa = Path(current_app.config["PRIPONKE_MAPA"])
    mapa.mkdir(parents=True, exist_ok=True)
    return mapa


def oddaj(uporabnik, id_opreme, id_ucilnice, naslov, opis, datoteke=None):
    """Odda novo prijavo težave (US-05, US-10). Vrne id prijave."""
    id_opreme = id_opreme or None
    id_ucilnice = id_ucilnice or None
    if id_opreme is None and id_ucilnice is None:
        raise PoslovnaNapaka("Izberi opremo, učilnico ali oboje.")
    if not (naslov or "").strip() or not (opis or "").strip():
        raise PoslovnaNapaka("Naslov in opis sta obvezna.")

    priponke = _preberi_priponke(datoteke)

    # Datoteke najprej zapišemo na disk pod naključnim imenom. Če shranjevanje
    # v bazo ne uspe, jih pobrišemo – tako ne ostane delna prijava.
    shranjene = []
    try:
        for izvirno_ime, vrsta, koncnica, vsebina in priponke:
            ime = secrets.token_hex(16) + koncnica
            (mapa_priponk() / ime).write_bytes(vsebina)
            shranjene.append((izvirno_ime, ime, vrsta, len(vsebina)))

        with transakcija() as k:
            if id_opreme is not None and repo_oprema.najdi(k, id_opreme) is None:
                raise PoslovnaNapaka("Izbrana oprema ne obstaja.")
            if id_ucilnice is not None and repo_ucilnice.najdi(k, id_ucilnice) is None:
                raise PoslovnaNapaka("Izbrana učilnica ne obstaja.")

            id_prijave = repo_prijave.ustvari(
                k, uporabnik.id, id_opreme, id_ucilnice, naslov.strip(), opis.strip()
            )
            for izvirno_ime, ime, vrsta, velikost in shranjene:
                repo_prijave.dodaj_priponko(k, id_prijave, izvirno_ime, ime, vrsta, velikost)
    except Exception:
        for _, ime, _, _ in shranjene:
            (mapa_priponk() / ime).unlink(missing_ok=True)
        raise

    return id_prijave


# --- Obravnava ---------------------------------------------------------------

def prevzemi(uporabnik, id_prijave):
    """IKT skrbnik prevzame novo prijavo (US-06)."""
    if not uporabnik.je_skrbnik:
        raise Prepovedano()

    with transakcija() as k:
        spremenjenih = repo_prijave.prevzemi(k, id_prijave, uporabnik.id, zdaj_utc())
        if spremenjenih == 0:
            if repo_prijave.najdi(k, id_prijave) is None:
                raise PoslovnaNapaka("Prijava ne obstaja.")
            raise PoslovnaNapaka("Prijavo je že prevzel drug skrbnik.")
        prijava = repo_prijave.najdi(k, id_prijave)
        prijavitelj = repo_uporabniki.najdi(k, prijava["prijavitelj_id"])

    obvestila.sprememba_prijave(prijava, prijavitelj["email"])


def zakljuci(uporabnik, id_prijave, resitev):
    """Odgovorni skrbnik ali administrator zaključi prijavo z rešitvijo (US-06)."""
    if not uporabnik.je_skrbnik:
        raise Prepovedano()
    resitev = (resitev or "").strip()

    with transakcija() as k:
        prijava = repo_prijave.zakleni(k, id_prijave)
        if prijava is None:
            raise PoslovnaNapaka("Prijava ne obstaja.")
        if prijava["skrbnik_id"] != uporabnik.id and not uporabnik.je_administrator:
            raise Prepovedano()
        if prijava["status"] != "v_obravnavi":
            raise PoslovnaNapaka("Zaključiti je mogoče samo prijavo v obravnavi.")
        if not resitev:
            raise PoslovnaNapaka("Pred zaključkom vnesi opis rešitve.")

        repo_prijave.zakljuci(k, id_prijave, resitev, zdaj_utc())
        prijava = repo_prijave.najdi(k, id_prijave)
        prijavitelj = repo_uporabniki.najdi(k, prijava["prijavitelj_id"])

    obvestila.sprememba_prijave(prijava, prijavitelj["email"])


def prerazporedi(uporabnik, id_prijave, id_novega_skrbnika):
    """Administrator dodeli prijavo v obravnavi drugemu skrbniku (US-06)."""
    if not uporabnik.je_administrator:
        raise Prepovedano()

    with transakcija() as k:
        prijava = repo_prijave.zakleni(k, id_prijave)
        if prijava is None:
            raise PoslovnaNapaka("Prijava ne obstaja.")
        if prijava["status"] != "v_obravnavi":
            raise PoslovnaNapaka("Prerazporediti je mogoče samo prijavo v obravnavi.")

        # Zaklenemo novega skrbnika, da ga medtem nihče ne deaktivira.
        novi = repo_uporabniki.zakleni(k, id_novega_skrbnika)
        if (novi is None or not novi["aktiven"]
                or novi["vloga"] not in ("ikt_skrbnik", "administrator")):
            raise PoslovnaNapaka("Prijavo lahko dodeliš samo aktivnemu IKT skrbniku ali administratorju.")

        repo_prijave.prerazporedi(k, id_prijave, id_novega_skrbnika)


def dodaj_komentar(uporabnik, id_prijave, besedilo):
    besedilo = (besedilo or "").strip()

    with transakcija() as k:
        prijava = repo_prijave.zakleni(k, id_prijave)
        if prijava is None:
            raise PoslovnaNapaka("Prijava ne obstaja.")
        dovoljeno = (
            prijava["prijavitelj_id"] == uporabnik.id
            or prijava["skrbnik_id"] == uporabnik.id
            or uporabnik.je_administrator
        )
        if not dovoljeno:
            raise Prepovedano()
        if prijava["status"] == "resena":
            raise PoslovnaNapaka("Pri rešeni prijavi novih komentarjev ni mogoče dodajati.")
        if not besedilo:
            raise PoslovnaNapaka("Komentar ne sme biti prazen.")

        repo_prijave.dodaj_komentar(k, id_prijave, uporabnik.id, besedilo)
