"""Upravljanje uporabniških računov (US-14, ADR-0005)."""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError
from werkzeug.security import generate_password_hash

from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import uporabniki as repo_uporabniki

VLOGE = ("ucitelj", "ikt_skrbnik", "administrator")
NAJMANJSA_DOLZINA_GESLA = 8


def _preveri_podatke(ime, priimek, email, vloga):
    if not ime or not priimek or not email:
        raise PoslovnaNapaka("Ime, priimek in e-poštni naslov so obvezni.")
    if vloga not in VLOGE:
        raise PoslovnaNapaka("Neveljavna vloga.")


def _preveri_geslo(geslo):
    if not geslo or len(geslo) < NAJMANJSA_DOLZINA_GESLA:
        raise PoslovnaNapaka(f"Geslo mora imeti vsaj {NAJMANJSA_DOLZINA_GESLA} znakov.")


def _napaka_email(email):
    return PoslovnaNapaka(f"E-poštni naslov {email} je že uporabljen.")


def ustvari(ime, priimek, email, geslo, vloga):
    """Ustvari račun. Geslo se shrani samo kot zgoščena vrednost. Vrne id.

    Kliče jo administrator v aplikaciji ali ukaz create-admin, zato tu ni
    preverjanja pravic – preveri jih klicatelj (glej ustvari_kot_administrator).
    """
    email = (email or "").strip().lower()
    _preveri_podatke(ime, priimek, email, vloga)
    _preveri_geslo(geslo)

    try:
        with transakcija() as k:
            if repo_uporabniki.najdi_po_emailu(k, email):
                raise _napaka_email(email)
            return repo_uporabniki.ustvari(k, ime, priimek, email, generate_password_hash(geslo),
                                           vloga)
    except IntegrityError as e:
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise _napaka_email(email) from e
        raise


def ustvari_kot_administrator(uporabnik, ime, priimek, email, geslo, vloga):
    if not uporabnik.je_administrator:
        raise Prepovedano()
    return ustvari(ime, priimek, email, geslo, vloga)


def posodobi(uporabnik, id_uporabnika, ime, priimek, email, vloga, aktiven, novo_geslo=None):
    """Administrator uredi račun, spremeni vlogo ali ga deaktivira.

    Pred odvzemom skrbniških pravic ali deaktivacijo morajo biti odprte
    prijave tega uporabnika prerazporejene (US-14).
    """
    if not uporabnik.je_administrator:
        raise Prepovedano()
    email = (email or "").strip().lower()
    _preveri_podatke(ime, priimek, email, vloga)
    if novo_geslo:
        _preveri_geslo(novo_geslo)

    try:
        with transakcija() as k:
            obstojeci = repo_uporabniki.zakleni(k, id_uporabnika)
            if obstojeci is None:
                raise PoslovnaNapaka("Uporabnik ne obstaja.")

            drug = repo_uporabniki.najdi_po_emailu(k, email)
            if drug and drug["id"] != id_uporabnika:
                raise _napaka_email(email)

            izgubi_skrbnistvo = (not aktiven) or vloga == "ucitelj"
            if izgubi_skrbnistvo and repo_uporabniki.stevilo_odprtih_prijav(k, id_uporabnika):
                raise PoslovnaNapaka(
                    "Uporabnik je odgovoren za odprte prijave. Najprej jih prerazporedi."
                )

            izgubi_admina = obstojeci["vloga"] == "administrator" and (
                not aktiven or vloga != "administrator"
            )
            if izgubi_admina and obstojeci["aktiven"] and repo_uporabniki.stevilo_administratorjev(k) <= 1:
                raise PoslovnaNapaka("V sistemu mora ostati vsaj en aktiven administrator.")

            repo_uporabniki.posodobi(k, id_uporabnika, ime, priimek, email, vloga, bool(aktiven))
            if novo_geslo:
                repo_uporabniki.nastavi_geslo(k, id_uporabnika, generate_password_hash(novo_geslo))
    except IntegrityError as e:
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise _napaka_email(email) from e
        raise
