"""Upravljanje uporabniških računov (US-14)."""

from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError
from werkzeug.security import generate_password_hash

from ..db import transakcija
from ..napake import PoslovnaNapaka, Prepovedano
from ..repositories import uporabniki as repo_uporabniki
from ..vloge import VLOGE

NAJMANJSA_DOLZINA_GESLA = 8


def _napaka_email(email):
    return PoslovnaNapaka(f"E-poštni naslov {email} je že uporabljen.")


def _pocisti_in_preveri(ime, priimek, email, vloga):
    """Odstrani presledke in preveri obvezne podatke. Vrne očiščene vrednosti."""
    ime = (ime or "").strip()
    priimek = (priimek or "").strip()
    email = (email or "").strip().lower()
    if not ime or not priimek or not email:
        raise PoslovnaNapaka("Ime, priimek in e-poštni naslov so obvezni.")
    if vloga not in VLOGE:
        raise PoslovnaNapaka("Neveljavna vloga.")
    return ime, priimek, email


def ustvari(ime, priimek, email, geslo, vloga):
    """Ustvari račun in vrne njegov id. Geslo se shrani samo kot zgoščena vrednost.

    Kliče jo ukaz create-admin ali administrator v aplikaciji. Pravice
    preveri klicatelj (pot je zaščitena z zahteva_vlogo("administrator")).
    """
    ime, priimek, email = _pocisti_in_preveri(ime, priimek, email, vloga)
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


def posodobi(uporabnik, id_uporabnika, ime, priimek, email, vloga, aktiven):
    """Administrator uredi podatke, spremeni vlogo ali deaktivira račun (US-14).

    - Uporabnik, ki ima prevzete odprte prijave, ne sme izgubiti skrbniških
      pravic (sprememba v učitelja ali deaktivacija), dokler prijave niso
      prerazporejene.
    - V sistemu mora ostati vsaj en aktiven administrator.
    - Računi se ne brišejo: rezervacije in prijave uporabnika ostanejo.
    """
    if not uporabnik.je_administrator:
        raise Prepovedano()
    ime, priimek, email = _pocisti_in_preveri(ime, priimek, email, vloga)
    aktiven = bool(aktiven)

    try:
        with transakcija() as k:
            obstojeci = repo_uporabniki.zakleni(k, id_uporabnika)
            if obstojeci is None:
                raise PoslovnaNapaka("Uporabnik ne obstaja.")

            drug = repo_uporabniki.najdi_po_emailu(k, email)
            if drug and drug["id"] != id_uporabnika:
                raise _napaka_email(email)

            izgubi_skrbnistvo = not aktiven or vloga == "ucitelj"
            if izgubi_skrbnistvo and repo_uporabniki.stevilo_odprtih_prijav(k, id_uporabnika):
                raise PoslovnaNapaka(
                    "Uporabnik ima prevzete odprte prijave. Najprej jih prerazporedi "
                    "drugemu IKT skrbniku."
                )

            je_bil_aktiven_admin = obstojeci["vloga"] == "administrator" and obstojeci["aktiven"]
            ostane_aktiven_admin = vloga == "administrator" and aktiven
            if (je_bil_aktiven_admin and not ostane_aktiven_admin
                    and repo_uporabniki.stevilo_aktivnih_administratorjev(k) <= 1):
                raise PoslovnaNapaka("V sistemu mora ostati vsaj en aktiven administrator.")

            repo_uporabniki.posodobi(k, id_uporabnika, ime, priimek, email, vloga, aktiven)
    except IntegrityError as e:
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise _napaka_email(email) from e
        raise
