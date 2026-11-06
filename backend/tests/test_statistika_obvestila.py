"""Testi statistike (US-12) in e-poštnih obvestil (US-11)."""

from datetime import date, timedelta

import pytest

from app.cas import v_lokalni, zdaj_utc
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import statistika as repo
from app.services import prijave as storitev_prijave
from app.services import rezervacije as storitev_rezervacije
from app.statistika import obdobje_v_utc, oblikuj_trajanje

from conftest import prijavi

H = timedelta(hours=1)


def _danasnje_obdobje():
    danes = v_lokalni(zdaj_utc()).date()
    return obdobje_v_utc(danes - timedelta(days=1), danes + timedelta(days=7))


def test_obdobje_vkljucuje_oba_datuma():
    od, do = obdobje_v_utc(date(2026, 12, 1), date(2026, 12, 31))
    # Lokalna polnoč pozimi = 23.00 UTC prejšnjega dne.
    assert od.isoformat() == "2026-11-30T23:00:00"
    assert do.isoformat() == "2026-12-31T23:00:00"


def test_statistika_brez_podatkov(app):
    od, do = _danasnje_obdobje()
    with transakcija() as k:
        assert repo.stevilo_prijav(k, od, do) == 0
        assert repo.povprecni_cas_resevanja(k, od, do) is None
    assert oblikuj_trajanje(None) == "Ni podatkov"


def test_prijava_z_opremo_in_ucilnico_se_v_skupnem_stevilu_steje_enkrat(
        ucitelj, skrbnik, projektor, ucilnica, jutri_ob_9):
    storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    id_preklicane = storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9 + H, jutri_ob_9 + 2 * H)
    storitev_rezervacije.preklici(ucitelj, id_preklicane)

    id_prijave = storitev_prijave.oddaj(ucitelj, projektor["id"], ucilnica["id"], "Napaka", "Opis")
    storitev_prijave.prevzemi(skrbnik, id_prijave)
    storitev_prijave.zakljuci(skrbnik, id_prijave, "Rešeno.")

    od, do = _danasnje_obdobje()
    with transakcija() as k:
        assert repo.stevilo_rezervacij(k, od, do) == 1  # preklicana se ne šteje
        assert repo.stevilo_prijav(k, od, do) == 1
        assert [v["stevilo"] for v in repo.prijave_po_opremi(k, od, do)] == [1]
        assert [v["stevilo"] for v in repo.prijave_po_ucilnicah(k, od, do)] == [1]
        assert repo.povprecni_cas_resevanja(k, od, do) is not None


def test_ucitelj_nima_dostopa_do_statistike(odjemalec, ucitelj):
    prijavi(odjemalec, ucitelj.email)
    assert odjemalec.get("/statistika/").status_code == 403


def test_obrnjen_interval_je_zavrnjen(odjemalec, skrbnik):
    prijavi(odjemalec, skrbnik.email)
    odgovor = odjemalec.get("/statistika/?od=2026-12-31&do=2026-12-01")
    assert "Začetni datum mora biti pred končnim" in odgovor.get_data(as_text=True)


# --- US-11: obvestila ------------------------------------------------------------

def _obvestila():
    with transakcija() as k:
        k.execute("SELECT prejemnik, zadeva, status FROM obvestilo ORDER BY id")
        return k.fetchall()


def test_obvestila_ob_rezervaciji_preklicu_in_spremembi_prijave(ucitelj, skrbnik, projektor, jutri_ob_9):
    id_rez = storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    storitev_rezervacije.preklici(ucitelj, id_rez)
    id_prijave = storitev_prijave.oddaj(ucitelj, projektor["id"], None, "Napaka", "Opis")
    storitev_prijave.prevzemi(skrbnik, id_prijave)
    storitev_prijave.zakljuci(skrbnik, id_prijave, "Rešeno.")

    obvestila = _obvestila()
    assert [o["prejemnik"] for o in obvestila] == [ucitelj.email] * 4
    assert "Potrjena rezervacija" in obvestila[0]["zadeva"]
    assert "Preklicana rezervacija" in obvestila[1]["zadeva"]
    assert "v obravnavi" in obvestila[2]["zadeva"]
    assert "rešena" in obvestila[3]["zadeva"]
    assert {o["status"] for o in obvestila} == {"samo_zabelezeno"}


def test_zavrnjena_operacija_ne_sprozi_obvestila(ucitelj, ucitelj2, projektor, jutri_ob_9):
    storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    with pytest.raises(PoslovnaNapaka):
        storitev_rezervacije.ustvari(ucitelj2, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    assert len(_obvestila()) == 1


def test_napaka_posiljanja_ne_razveljavi_rezervacije(app, ucitelj, projektor, jutri_ob_9):
    # Neobstoječ poštni strežnik: pošiljanje ne uspe, rezervacija pa ostane.
    app.config.update(MAIL_SERVER="127.0.0.1", MAIL_PORT=1, MAIL_USE_TLS=False)
    storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)

    with transakcija() as k:
        k.execute("SELECT COUNT(*) AS n FROM rezervacija")
        assert k.fetchone()["n"] == 1
    assert _obvestila()[0]["status"] == "napaka"
