"""E-poštna obvestila (nadgradnja F11, US-11).

Obvestilo se pošlje šele PO uspešno potrjeni transakciji, zato zavrnjena
operacija nikoli ne sproži obvestila o uspehu.

Če v .env ni nastavljen MAIL_SERVER, se obvestilo samo zabeleži v tabelo
obvestilo (status 'samo_zabelezeno') – tako lahko obvestila pregledamo v
aplikaciji tudi brez poštnega strežnika. Napaka pri pošiljanju se zabeleži,
nikoli pa ne razveljavi že shranjene rezervacije ali spremembe prijave.
"""

import smtplib
from email.message import EmailMessage

from flask import current_app

from ..cas import oblikuj
from ..db import transakcija
from ..repositories import obvestila as repo_obvestila


def poslji(prejemnik, zadeva, besedilo):
    """Pošlje (ali samo zabeleži) obvestilo. Nikoli ne sproži napake."""
    try:
        status, napaka = _poslji_po_posti(prejemnik, zadeva, besedilo)
    except Exception as e:  # noqa: BLE001 – katerakoli napaka pošiljanja
        status, napaka = "napaka", str(e)
        current_app.logger.warning("Pošiljanje obvestila na %s ni uspelo: %s", prejemnik, e)

    try:
        with transakcija() as k:
            repo_obvestila.zabelezi(k, prejemnik, zadeva[:200], besedilo, status, napaka)
    except Exception as e:  # noqa: BLE001
        current_app.logger.error("Obvestila ni bilo mogoče zabeležiti: %s", e)


def _poslji_po_posti(prejemnik, zadeva, besedilo):
    config = current_app.config
    if not config.get("MAIL_SERVER"):
        return "samo_zabelezeno", None

    sporocilo = EmailMessage()
    sporocilo["From"] = config["MAIL_SENDER"]
    sporocilo["To"] = prejemnik
    sporocilo["Subject"] = zadeva
    sporocilo.set_content(besedilo)

    with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as streznik:
        if config.get("MAIL_USE_TLS"):
            streznik.starttls()
        if config.get("MAIL_USERNAME"):
            streznik.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
        streznik.send_message(sporocilo)
    return "poslano", None


def _povezava(pot):
    return current_app.config.get("APP_URL", "http://127.0.0.1:5000").rstrip("/") + pot


# --- Besedila obvestil -------------------------------------------------------

def nova_rezervacija(rezervacija, email):
    poslji(
        email,
        f"Potrjena rezervacija: {rezervacija['oprema_naziv']}",
        f"Rezervacija je potrjena.\n\n"
        f"Oprema: {rezervacija['oprema_naziv']} ({rezervacija['inventarna_stevilka']})\n"
        f"Termin: {oblikuj(rezervacija['zacetek'])} – {oblikuj(rezervacija['konec'])}\n\n"
        f"Moje rezervacije: {_povezava('/rezervacije/moje')}\n",
    )


def preklicana_rezervacija(rezervacija, email):
    razlog = rezervacija["razlog_preklica"] or "ni naveden"
    poslji(
        email,
        f"Preklicana rezervacija: {rezervacija['oprema_naziv']}",
        f"Rezervacija je bila preklicana.\n\n"
        f"Oprema: {rezervacija['oprema_naziv']} ({rezervacija['inventarna_stevilka']})\n"
        f"Termin: {oblikuj(rezervacija['zacetek'])} – {oblikuj(rezervacija['konec'])}\n"
        f"Razlog: {razlog}\n",
    )


NAZIVI_STATUSOV = {"nova": "nova", "v_obravnavi": "v obravnavi", "resena": "rešena"}


def sprememba_prijave(prijava, email):
    status = NAZIVI_STATUSOV[prijava["status"]]
    povezava = _povezava(f"/prijave/{prijava['id']}")
    poslji(
        email,
        f"Prijava #{prijava['id']} je {status}",
        f"Stanje tvoje prijave »{prijava['naslov']}« (#{prijava['id']}) je zdaj: {status}.\n\n"
        f"Podrobnosti: {povezava}\n",
    )
