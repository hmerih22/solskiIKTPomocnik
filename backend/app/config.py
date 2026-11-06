"""Nalaganje nastavitev aplikacije iz okoljskih spremenljivk (.env)."""

import os

from dotenv import load_dotenv

# Obvezne nastavitve: brez njih aplikacija ne sme začeti delovati.
OBVEZNE_NASTAVITVE = ["SECRET_KEY", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


class ManjkajocaNastavitev(RuntimeError):
    """Napaka, ko v okolju manjka obvezna nastavitev."""


def nalozi_nastavitve():
    """Prebere .env in vrne slovar nastavitev za Flask.

    Če katera obvezna nastavitev manjka ali je prazna, sproži jasno napako,
    namesto da bi aplikacija tiho uporabila privzet (nevaren) skrivni ključ.
    """
    load_dotenv()

    manjkajoce = [ime for ime in OBVEZNE_NASTAVITVE if not os.environ.get(ime)]
    if manjkajoce:
        raise ManjkajocaNastavitev(
            "V datoteki .env manjkajo obvezne nastavitve: "
            + ", ".join(manjkajoce)
            + ". Kopiraj .env.example v .env in jih izpolni."
        )

    return {
        "SECRET_KEY": os.environ["SECRET_KEY"],
        "DB_HOST": os.environ["DB_HOST"],
        "DB_PORT": int(os.environ["DB_PORT"]),
        "DB_NAME": os.environ["DB_NAME"],
        "DB_USER": os.environ["DB_USER"],
        "DB_PASSWORD": os.environ["DB_PASSWORD"],
        # Neobvezne nastavitve (nadgradnje). Brez MAIL_SERVER se obvestila
        # samo zabeležijo v bazo in ne pošiljajo.
        "APP_URL": os.environ.get("APP_URL", "http://127.0.0.1:5000"),
        "MAIL_SERVER": os.environ.get("MAIL_SERVER", ""),
        "MAIL_PORT": int(os.environ.get("MAIL_PORT") or 587),
        "MAIL_USE_TLS": os.environ.get("MAIL_USE_TLS", "1") == "1",
        "MAIL_USERNAME": os.environ.get("MAIL_USERNAME", ""),
        "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD", ""),
        "MAIL_SENDER": os.environ.get("MAIL_SENDER", "ikt-pomocnik@sola.si"),
    }
