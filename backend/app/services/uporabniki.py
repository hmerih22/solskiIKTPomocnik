"""Upravljanje uporabniških računov (US-14)."""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError
from werkzeug.security import generate_password_hash

from ..vloge import VLOGE
from ..db import transakcija
from ..napake import PoslovnaNapaka
from ..repositories import uporabniki as repo_uporabniki

NAJMANJSA_DOLZINA_GESLA = 8


def _napaka_email(email):
    return PoslovnaNapaka(f"E-poštni naslov {email} je že uporabljen.")


def ustvari(ime, priimek, email, geslo, vloga):
  
    ime = (ime or "").strip()
    priimek = (priimek or "").strip()
    email = (email or "").strip().lower()

    if not ime or not priimek or not email:
        raise PoslovnaNapaka("Ime, priimek in e-poštni naslov so obvezni.")
    if vloga not in VLOGE:
        raise PoslovnaNapaka("Neveljavna vloga.")
    if not geslo or len(geslo) < NAJMANJSA_DOLZINA_GESLA:
        raise PoslovnaNapaka(f"Geslo mora imeti vsaj {NAJMANJSA_DOLZINA_GESLA} znakov.")

    try:
        with transakcija() as k:
            if repo_uporabniki.najdi_po_emailu(k, email):
                raise _napaka_email(email)
            return repo_uporabniki.ustvari(k, ime, priimek, email,
                                           generate_password_hash(geslo), vloga)
    except IntegrityError as e:
        # Dva sočasna vnosa iste e-pošte: drugega zavrne omejitev UNIQUE.
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise _napaka_email(email) from e
        raise
