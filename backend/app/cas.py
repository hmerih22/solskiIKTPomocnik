"""Pretvorbe časa med UTC (baza) in lokalnim časom (uporabnik).

Baza hrani vse čase v stolpcih DATETIME brez časovnega pasu, po dogovoru v UTC.
Uporabnik vnaša in vidi čas v pasu Europe/Ljubljana (poletni/zimski čas).

Pravilo v kodi: v Pythonu vedno delamo z "naivnimi" datetime objekti v UTC
(brez tzinfo), ker jih tako vrača in sprejema MySQL Connector. Lokalni čas
nastopa samo na robu: pri branju obrazca (v_utc) in pri prikazu (v_lokalni).
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOKALNI_PAS = ZoneInfo("Europe/Ljubljana")


def zdaj_utc():
    """Trenutni čas v UTC kot naiven datetime (enako kot v bazi)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def v_utc(lokalni):
    """Lokalni čas iz obrazca (naiven, Europe/Ljubljana) pretvori v naiven UTC."""
    if lokalni is None:
        return None
    return lokalni.replace(tzinfo=LOKALNI_PAS).astimezone(timezone.utc).replace(tzinfo=None)


def v_lokalni(utc):
    """Naiven UTC čas iz baze pretvori v lokalni čas (z informacijo o pasu)."""
    if utc is None:
        return None
    return utc.replace(tzinfo=timezone.utc).astimezone(LOKALNI_PAS)


def oblikuj(utc, oblika="%d. %m. %Y %H:%M"):
    """Jinja filter: UTC iz baze prikaže kot lokalni čas, npr. 06. 11. 2026 09:00."""
    if utc is None:
        return ""
    return v_lokalni(utc).strftime(oblika)


def za_obrazec(utc):
    """UTC iz baze pretvori v lokalni naiven čas za predizpolnitev obrazca."""
    if utc is None:
        return None
    return v_lokalni(utc).replace(tzinfo=None)
