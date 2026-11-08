"""Upravljanje povezave z MySQL bazo.

Vsaka zahteva dobi svojo povezavo, ki se odpre ob prvi uporabi (get_db)
in se samodejno zapre ob koncu zahteve (close_db). Samodejno potrjevanje
(autocommit) je izklopljeno: spremembe je treba potrditi z commit() ali
uporabiti pomočnika transakcija().

Nastavitve povezave (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) se
preberejo iz app.config, ki jih napolni config.nalozi_nastavitve() iz .env.
"""

from contextlib import contextmanager

import mysql.connector
from flask import current_app, g

from .config import ManjkajocaNastavitev

NASTAVITVE_BAZE = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def _odpri_povezavo(config):
    """Odpre novo povezavo z bazo glede na podane nastavitve."""
    manjkajoce = [ime for ime in NASTAVITVE_BAZE if not config.get(ime)]
    if manjkajoce:
        raise ManjkajocaNastavitev(
            "Za povezavo z bazo manjkajo nastavitve: " + ", ".join(manjkajoce) + "."
        )

    povezava = mysql.connector.connect(
        host=config["DB_HOST"],
        port=int(config["DB_PORT"]),
        database=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        charset="utf8mb4",
        collation="utf8mb4_0900_ai_ci",
        autocommit=False,
        # Vsi časi v bazi so v UTC (glej 001-schema.sql).
        time_zone="+00:00",
    )
    return povezava


def get_db():
    """Vrne povezavo za trenutno zahtevo; ob prvem klicu jo odpre."""
    if "db" not in g:
        g.db = _odpri_povezavo(current_app.config)
    return g.db


def close_db(napaka=None):
    """Ob koncu zahteve razveljavi nepotrjeno transakcijo in zapre povezavo.

    Razveljavitev se izvede vedno, ne le ob napaki: kar ni bilo izrecno
    potrjeno s commit(), se ne sme shraniti.
    """
    povezava = g.pop("db", None)
    if povezava is None:
        return

    try:
        if povezava.is_connected():
            povezava.rollback()
    finally:
        povezava.close()


@contextmanager
def transakcija():
    """Izvede blok kot eno transakcijo in vrne kazalec (cursor).

    Če se blok konča brez napake, se spremembe potrdijo; ob napaki se
    razveljavijo in napaka se posreduje naprej. Primer:

        with transakcija() as kazalec:
            kazalec.execute("UPDATE ... WHERE id = %s", (id_opreme,))
    """
    povezava = get_db()
    kazalec = povezava.cursor(dictionary=True)
    try:
        yield kazalec
        povezava.commit()
    except Exception:
        povezava.rollback()
        raise
    finally:
        kazalec.close()


def init_app(app):
    """Poveže upravljanje baze z aplikacijo."""
    app.teardown_appcontext(close_db)
