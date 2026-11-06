"""Testi rezervacij (US-02, US-03, US-04, US-07, US-08)."""

import threading
from datetime import timedelta

import pytest

from app.cas import zdaj_utc
from app.db import transakcija
from app.napake import PoslovnaNapaka, Prepovedano
from app.repositories import oprema as repo_oprema
from app.repositories import rezervacije as repo_rezervacije
from app.services import oprema as storitev_oprema
from app.services import rezervacije as storitev

from conftest import prijavi

H = timedelta(hours=1)


def _aktivne(id_opreme):
    with transakcija() as k:
        k.execute("SELECT COUNT(*) AS n FROM rezervacija WHERE oprema_id = %s AND status = 'aktivna'",
                  (id_opreme,))
        return k.fetchone()["n"]


# --- US-02 / US-03: prekrivanje ----------------------------------------------

def test_ucitelj_rezervira_prost_projektor(ucitelj, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    with transakcija() as k:
        rez = repo_rezervacije.najdi(k, id_rez)
    assert rez["uporabnik_id"] == ucitelj.id
    assert rez["status"] == "aktivna"


def test_prekrivajoci_termin_je_zaseden_sosednji_pa_prost(ucitelj, ucitelj2, projektor, jutri_ob_9):
    storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)  # 9.00–10.00

    for zacetek, konec in [(jutri_ob_9, jutri_ob_9 + H),                      # isti termin
                           (jutri_ob_9 + H / 2, jutri_ob_9 + H * 1.5)]:       # 9.30–10.30
        assert not storitev.preveri_razpolozljivost(projektor["id"], zacetek, konec)["prosta"]
        with pytest.raises(PoslovnaNapaka, match="zasedel"):
            storitev.ustvari(ucitelj2, projektor["id"], zacetek, konec)

    # 10.00–11.00 se začne natanko ob koncu obstoječe – dovoljeno.
    assert storitev.preveri_razpolozljivost(projektor["id"], jutri_ob_9 + H, jutri_ob_9 + 2 * H)["prosta"]
    storitev.ustvari(ucitelj2, projektor["id"], jutri_ob_9 + H, jutri_ob_9 + 2 * H)
    assert _aktivne(projektor["id"]) == 2


def test_preklicana_rezervacija_ne_zaseda_termina(ucitelj, ucitelj2, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    storitev.preklici(ucitelj, id_rez)
    assert storitev.preveri_razpolozljivost(projektor["id"], jutri_ob_9, jutri_ob_9 + H)["prosta"]
    storitev.ustvari(ucitelj2, projektor["id"], jutri_ob_9, jutri_ob_9 + H)


@pytest.mark.parametrize("zamik_zacetka, trajanje", [
    (-timedelta(hours=30), H),   # začetek v preteklosti
    (timedelta(0), timedelta(0)),  # začetek = konec
    (timedelta(0), -H),          # konec pred začetkom
])
def test_neveljaven_termin_je_zavrnjen(ucitelj, projektor, jutri_ob_9, zamik_zacetka, trajanje):
    zacetek = jutri_ob_9 + zamik_zacetka
    with pytest.raises(PoslovnaNapaka):
        storitev.ustvari(ucitelj, projektor["id"], zacetek, zacetek + trajanje)
    assert _aktivne(projektor["id"]) == 0


def test_socasni_rezervaciji_iste_opreme_uspe_samo_ena(app, ucitelj, ucitelj2, projektor, jutri_ob_9):
    """Dve niti hkrati oddata prekrivajoči rezervaciji – zaklep opreme dovoli samo eno."""
    ovira = threading.Barrier(2)
    rezultati = []

    def rezerviraj(uporabnik, zamik):
        with app.app_context():
            ovira.wait()  # obe niti začneta hkrati
            try:
                storitev.ustvari(uporabnik, projektor["id"], jutri_ob_9 + zamik, jutri_ob_9 + zamik + H)
                rezultati.append("uspeh")
            except PoslovnaNapaka:
                rezultati.append("zavrnjeno")

    niti = [threading.Thread(target=rezerviraj, args=(ucitelj, timedelta(0))),
            threading.Thread(target=rezerviraj, args=(ucitelj2, timedelta(minutes=30)))]
    for nit in niti:
        nit.start()
    for nit in niti:
        nit.join(timeout=30)

    assert sorted(rezultati) == ["uspeh", "zavrnjeno"]
    assert _aktivne(projektor["id"]) == 1


def test_rezervacija_prek_obrazca(odjemalec, ucitelj, projektor, jutri_ob_9):
    prijavi(odjemalec, ucitelj.email)
    # Obrazec sprejme lokalni čas; izberemo termin čez dva dni ob 10.00.
    dan = (jutri_ob_9 + timedelta(days=1)).strftime("%Y-%m-%d")
    podatki = {"zacetek": f"{dan}T10:00", "konec": f"{dan}T11:00"}

    odgovor = odjemalec.post(f"/rezervacije/nova/{projektor['id']}", data={**podatki, "preveri": "1"})
    assert "prosta" in odgovor.get_data(as_text=True)
    assert _aktivne(projektor["id"]) == 0  # preverjanje ne ustvari rezervacije

    odgovor = odjemalec.post(f"/rezervacije/nova/{projektor['id']}", data={**podatki, "potrdi": "1"},
                             follow_redirects=True)
    assert "Rezervacija je potrjena" in odgovor.get_data(as_text=True)
    assert _aktivne(projektor["id"]) == 1


# --- US-07: nedelujoča oprema ------------------------------------------------

def test_nedelujoce_opreme_ni_mogoce_rezervirati(ucitelj, skrbnik, projektor, jutri_ob_9):
    storitev_oprema.spremeni_stanje(skrbnik, projektor["id"], "nedelujoca")
    assert not storitev.preveri_razpolozljivost(projektor["id"], jutri_ob_9, jutri_ob_9 + H)["prosta"]
    with pytest.raises(PoslovnaNapaka, match="nedelujoča"):
        storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)


def test_obstojeca_rezervacija_ostane_z_opozorilom(odjemalec, ucitelj, skrbnik, projektor, jutri_ob_9):
    storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    prihodnje = storitev_oprema.spremeni_stanje(skrbnik, projektor["id"], "nedelujoca")
    assert prihodnje == 1
    assert _aktivne(projektor["id"]) == 1  # ni samodejno preklicana

    prijavi(odjemalec, ucitelj.email)
    assert "Oprema je označena kot nedelujoča" in odgovor_besedilo(odjemalec, "/rezervacije/moje")

    storitev_oprema.spremeni_stanje(skrbnik, projektor["id"], "uporabna")
    assert "Oprema je označena kot nedelujoča" not in odgovor_besedilo(odjemalec, "/rezervacije/moje")


def test_ucitelj_ne_more_spremeniti_stanja_opreme(odjemalec, ucitelj, projektor):
    prijavi(odjemalec, ucitelj.email)
    odgovor = odjemalec.post(f"/oprema/{projektor['id']}/stanje", data={"stanje": "nedelujoca"})
    assert odgovor.status_code == 403
    with transakcija() as k:
        assert repo_oprema.najdi(k, projektor["id"])["stanje"] == "uporabna"


# --- US-04: preklic ------------------------------------------------------------

def test_ucitelj_ne_more_preklicati_tuje_rezervacije(odjemalec, ucitelj, ucitelj2, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    prijavi(odjemalec, ucitelj2.email)
    odgovor = odjemalec.post(f"/rezervacije/{id_rez}/preklic", data={"razlog": "x"})
    assert odgovor.status_code == 403
    assert _aktivne(projektor["id"]) == 1


def test_ze_zacete_rezervacije_ni_mogoce_preklicati(ucitelj, projektor):
    zdaj = zdaj_utc()
    with transakcija() as k:
        id_rez = repo_rezervacije.ustvari(k, ucitelj.id, projektor["id"], zdaj - H, zdaj + H)
    with pytest.raises(PoslovnaNapaka, match="že začela"):
        storitev.preklici(ucitelj, id_rez)


def test_dvojni_preklic_je_zavrnjen(ucitelj, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    storitev.preklici(ucitelj, id_rez)
    with pytest.raises(PoslovnaNapaka, match="že preklicana"):
        storitev.preklici(ucitelj, id_rez)


def test_skrbnik_preklice_samo_rezervacijo_nedelujoce_opreme_z_razlogom(
        ucitelj, skrbnik, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    with pytest.raises(Prepovedano):
        storitev.preklici(skrbnik, id_rez, "razlog")  # oprema še deluje

    storitev_oprema.spremeni_stanje(skrbnik, projektor["id"], "nedelujoca")
    with pytest.raises(PoslovnaNapaka, match="razlog"):
        storitev.preklici(skrbnik, id_rez, "   ")
    storitev.preklici(skrbnik, id_rez, "Projektor je v servisu.")

    with transakcija() as k:
        rez = repo_rezervacije.najdi(k, id_rez)
    assert rez["status"] == "preklicana"
    assert rez["preklical_id"] == skrbnik.id
    assert rez["razlog_preklica"] == "Projektor je v servisu."


def test_administrator_preklice_katerokoli_rezervacijo_z_razlogom(ucitelj, admin, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    with pytest.raises(PoslovnaNapaka):
        storitev.preklici(admin, id_rez, None)
    storitev.preklici(admin, id_rez, "Šolski dogodek.")
    assert _aktivne(projektor["id"]) == 0


# --- US-08: prevzem in vračilo -------------------------------------------------

def test_prevzem_in_vracilo(ucitelj, skrbnik, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)

    with pytest.raises(PoslovnaNapaka, match="šele po prevzemu"):
        storitev.zabelezi_vracilo(skrbnik, id_rez)
    storitev.zabelezi_prevzem(skrbnik, id_rez)
    with pytest.raises(PoslovnaNapaka, match="že zabeležen"):
        storitev.zabelezi_prevzem(skrbnik, id_rez)

    # Iste opreme ni mogoče izdati pri drugi rezervaciji, dokler ni vrnjena.
    id_druga = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9 + H, jutri_ob_9 + 2 * H)
    with pytest.raises(PoslovnaNapaka, match="izposojena"):
        storitev.zabelezi_prevzem(skrbnik, id_druga)

    storitev.zabelezi_vracilo(skrbnik, id_rez)
    with pytest.raises(PoslovnaNapaka, match="že zabeleženo"):
        storitev.zabelezi_vracilo(skrbnik, id_rez)
    storitev.zabelezi_prevzem(skrbnik, id_druga)


def test_preklicane_rezervacije_ni_mogoce_prevzeti(ucitelj, skrbnik, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    storitev.preklici(ucitelj, id_rez)
    with pytest.raises(PoslovnaNapaka, match="Preklicane"):
        storitev.zabelezi_prevzem(skrbnik, id_rez)


def test_zamuda_pri_vracilu_je_prikazana(odjemalec, ucitelj, skrbnik, projektor):
    zdaj = zdaj_utc()
    with transakcija() as k:
        id_rez = repo_rezervacije.ustvari(k, ucitelj.id, projektor["id"], zdaj - 3 * H, zdaj - H)
        repo_rezervacije.zabelezi_prevzem(k, id_rez, zdaj - 3 * H)
    prijavi(odjemalec, skrbnik.email)
    assert "Zamuda pri vračilu" in odgovor_besedilo(odjemalec, "/rezervacije/izposoja")


def test_ucitelj_ne_more_zabeleziti_prevzema(odjemalec, ucitelj, projektor, jutri_ob_9):
    id_rez = storitev.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9 + H)
    prijavi(odjemalec, ucitelj.email)
    assert odjemalec.post(f"/rezervacije/{id_rez}/prevzem").status_code == 403


def odgovor_besedilo(odjemalec, pot):
    odgovor = odjemalec.get(pot)
    assert odgovor.status_code == 200
    return odgovor.get_data(as_text=True)
