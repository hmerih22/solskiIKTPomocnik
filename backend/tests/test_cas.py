"""Testi pretvorbe časa in validacije termina (US-02). Ne potrebujejo baze."""

from datetime import datetime, timedelta

import pytest

from app.cas import oblikuj, v_lokalni, v_utc, za_obrazec
from app.napake import PoslovnaNapaka
from app.services.rezervacije import preveri_termin


def test_pretvorba_pozimi():
    # Pozimi je Ljubljana UTC+1.
    assert v_utc(datetime(2026, 12, 1, 9, 0)) == datetime(2026, 12, 1, 8, 0)


def test_pretvorba_poleti():
    # Poleti (poletni čas) je Ljubljana UTC+2.
    assert v_utc(datetime(2026, 7, 1, 9, 0)) == datetime(2026, 7, 1, 7, 0)


def test_pretvorba_tja_in_nazaj():
    lokalni = datetime(2026, 11, 10, 14, 30)
    assert za_obrazec(v_utc(lokalni)) == lokalni
    assert v_lokalni(v_utc(lokalni)).hour == 14


def test_prikaz_v_lokalnem_casu():
    assert oblikuj(datetime(2026, 11, 10, 8, 0)) == "10. 11. 2026 09:00"
    assert oblikuj(None) == ""


ZDAJ = datetime(2026, 11, 10, 8, 0)


def test_veljaven_termin():
    preveri_termin(ZDAJ + timedelta(hours=1), ZDAJ + timedelta(hours=2), zdaj=ZDAJ)


@pytest.mark.parametrize("zacetek, konec, sporocilo", [
    (ZDAJ + timedelta(hours=2), ZDAJ + timedelta(hours=1), "pred koncem"),
    (ZDAJ + timedelta(hours=1), ZDAJ + timedelta(hours=1), "pred koncem"),
    (ZDAJ - timedelta(hours=1), ZDAJ + timedelta(hours=1), "v prihodnosti"),
    (ZDAJ, ZDAJ + timedelta(hours=1), "v prihodnosti"),
    (None, ZDAJ, "Vnesi"),
])
def test_neveljaven_termin(zacetek, konec, sporocilo):
    with pytest.raises(PoslovnaNapaka, match=sporocilo):
        preveri_termin(zacetek, konec, zdaj=ZDAJ)
