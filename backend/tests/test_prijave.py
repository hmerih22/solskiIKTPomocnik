"""Testi prijav težav (US-05, US-06, US-09, US-10)."""

import io
import threading

import pytest

from app.db import transakcija
from app.napake import PoslovnaNapaka, Prepovedano
from app.repositories import oprema as repo_oprema
from app.repositories import prijave as repo_prijave
from app.services import prijave as storitev

from conftest import prijavi

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
PDF = b"%PDF-1.4\n" + b"x" * 100


def _prijava(id_prijave):
    with transakcija() as k:
        return repo_prijave.najdi(k, id_prijave)


def _stevilo_prijav():
    with transakcija() as k:
        k.execute("SELECT COUNT(*) AS n FROM prijava_tezave")
        return k.fetchone()["n"]


@pytest.fixture
def nova_prijava(ucitelj, projektor):
    return storitev.oddaj(ucitelj, projektor["id"], None, "Ne prižge", "Lučka utripa.")


# --- US-05: oddaja in pregled --------------------------------------------------

def test_prijava_brez_opreme_in_ucilnice_je_zavrnjena(ucitelj):
    with pytest.raises(PoslovnaNapaka, match="opremo, učilnico"):
        storitev.oddaj(ucitelj, None, None, "Naslov", "Opis")
    assert _stevilo_prijav() == 0


def test_prijava_samo_na_ucilnici_in_samo_na_opremi(ucitelj, ucilnica, projektor):
    id_ucilnica = storitev.oddaj(ucitelj, None, ucilnica["id"], "Ni interneta", "Wi-Fi ne deluje.")
    id_oprema = storitev.oddaj(ucitelj, projektor["id"], None, "Ne prižge", "Lučka utripa.")

    for id_prijave in (id_ucilnica, id_oprema):
        prijava = _prijava(id_prijave)
        assert prijava["status"] == "nova"
        assert prijava["prijavitelj_id"] == ucitelj.id
        assert prijava["skrbnik_id"] is None


def test_prijava_prek_obrazca_s_presledki_je_zavrnjena(odjemalec, ucitelj, projektor):
    prijavi(odjemalec, ucitelj.email)
    odgovor = odjemalec.post("/prijave/nova", data={
        "naslov": "   ", "opis": "Opis", "oprema_id": projektor["id"], "ucilnica_id": 0})
    assert "To polje je obvezno" in odgovor.get_data(as_text=True)
    assert _stevilo_prijav() == 0


def test_ucitelj_ne_vidi_tuje_prijave(odjemalec, ucitelj2, nova_prijava):
    prijavi(odjemalec, ucitelj2.email)
    assert odjemalec.get(f"/prijave/{nova_prijava}").status_code == 403


def test_prijavitelj_vidi_svojo_prijavo(odjemalec, ucitelj, nova_prijava):
    prijavi(odjemalec, ucitelj.email)
    odgovor = odjemalec.get(f"/prijave/{nova_prijava}")
    assert odgovor.status_code == 200
    assert "Lučka utripa." in odgovor.get_data(as_text=True)


# --- US-06: prevzem in zaključek -----------------------------------------------

def test_prevzem_in_zakljucek_z_resitvijo(ucitelj, skrbnik, nova_prijava):
    storitev.prevzemi(skrbnik, nova_prijava)
    prijava = _prijava(nova_prijava)
    assert prijava["status"] == "v_obravnavi"
    assert prijava["skrbnik_id"] == skrbnik.id
    assert prijava["prevzeta_ob"] is not None

    with pytest.raises(PoslovnaNapaka, match="opis rešitve"):
        storitev.zakljuci(skrbnik, nova_prijava, "   ")
    assert _prijava(nova_prijava)["status"] == "v_obravnavi"

    storitev.zakljuci(skrbnik, nova_prijava, "Zamenjana žarnica.")
    prijava = _prijava(nova_prijava)
    assert prijava["status"] == "resena"
    assert prijava["resitev"] == "Zamenjana žarnica."
    assert prijava["resena_ob"] is not None


def test_drugi_skrbnik_ne_more_prevzeti_ali_zakljuciti(skrbnik, skrbnik2, nova_prijava):
    storitev.prevzemi(skrbnik, nova_prijava)
    with pytest.raises(PoslovnaNapaka, match="že prevzel"):
        storitev.prevzemi(skrbnik2, nova_prijava)
    with pytest.raises(Prepovedano):
        storitev.zakljuci(skrbnik2, nova_prijava, "Rešeno.")


def test_socasni_prevzem_potrdi_samo_enega(app, skrbnik, skrbnik2, nova_prijava):
    ovira = threading.Barrier(2)
    rezultati = []

    def prevzemi(uporabnik):
        with app.app_context():
            ovira.wait()
            try:
                storitev.prevzemi(uporabnik, nova_prijava)
                rezultati.append("uspeh")
            except PoslovnaNapaka:
                rezultati.append("ze_prevzeta")

    niti = [threading.Thread(target=prevzemi, args=(s,)) for s in (skrbnik, skrbnik2)]
    for nit in niti:
        nit.start()
    for nit in niti:
        nit.join(timeout=30)

    assert sorted(rezultati) == ["uspeh", "ze_prevzeta"]


def test_ucitelj_ne_more_prevzeti_ali_zakljuciti_prek_zahteve(odjemalec, ucitelj, nova_prijava):
    prijavi(odjemalec, ucitelj.email)
    assert odjemalec.post(f"/prijave/{nova_prijava}/prevzem").status_code == 403
    assert odjemalec.post(f"/prijave/{nova_prijava}/zakljucek",
                          data={"resitev": "x"}).status_code == 403
    assert _prijava(nova_prijava)["status"] == "nova"


def test_administrator_prerazporedi_in_ohrani_cas_prevzema(admin, skrbnik, skrbnik2, ucitelj, nova_prijava):
    storitev.prevzemi(skrbnik, nova_prijava)
    prevzeta_ob = _prijava(nova_prijava)["prevzeta_ob"]

    with pytest.raises(Prepovedano):
        storitev.prerazporedi(skrbnik, nova_prijava, skrbnik2.id)
    with pytest.raises(PoslovnaNapaka, match="aktivnemu IKT skrbniku"):
        storitev.prerazporedi(admin, nova_prijava, ucitelj.id)

    storitev.prerazporedi(admin, nova_prijava, skrbnik2.id)
    prijava = _prijava(nova_prijava)
    assert prijava["skrbnik_id"] == skrbnik2.id
    assert prijava["prevzeta_ob"] == prevzeta_ob
    # Administrator lahko zaključi tudi prijavo, ki je ne obravnava sam.
    storitev.zakljuci(admin, nova_prijava, "Rešeno.")


def test_zakljucek_prijave_ne_spremeni_stanja_opreme(skrbnik, projektor, nova_prijava):
    storitev.prevzemi(skrbnik, nova_prijava)
    storitev.zakljuci(skrbnik, nova_prijava, "Rešeno.")
    with transakcija() as k:
        assert repo_oprema.najdi(k, projektor["id"])["stanje"] == "uporabna"


# --- US-09: komentarji ---------------------------------------------------------

def test_komentarji(ucitelj, ucitelj2, skrbnik, nova_prijava):
    storitev.dodaj_komentar(ucitelj, nova_prijava, "Prvi komentar")
    storitev.prevzemi(skrbnik, nova_prijava)
    storitev.dodaj_komentar(skrbnik, nova_prijava, "Drugi komentar")

    with pytest.raises(Prepovedano):
        storitev.dodaj_komentar(ucitelj2, nova_prijava, "Tuj komentar")
    with pytest.raises(PoslovnaNapaka):
        storitev.dodaj_komentar(ucitelj, nova_prijava, "   ")

    storitev.zakljuci(skrbnik, nova_prijava, "Rešeno.")
    with pytest.raises(PoslovnaNapaka, match="rešeni"):
        storitev.dodaj_komentar(ucitelj, nova_prijava, "Prepozno")

    with transakcija() as k:
        komentarji = repo_prijave.komentarji(k, nova_prijava)
    assert [c["besedilo"] for c in komentarji] == ["Prvi komentar", "Drugi komentar"]


# --- US-10: priponke -----------------------------------------------------------

def _oddaj_s_priponkami(odjemalec, projektor, datoteke):
    return odjemalec.post("/prijave/nova", content_type="multipart/form-data", data={
        "naslov": "Napaka", "opis": "Opis", "oprema_id": projektor["id"], "ucilnica_id": 0,
        "priponke": [(io.BytesIO(vsebina), ime) for ime, vsebina in datoteke],
    }, follow_redirects=True)


def test_priponke_so_sprejete_in_dostopne_samo_upravicenim(
        odjemalec, app, ucitelj, ucitelj2, skrbnik, projektor):
    prijavi(odjemalec, ucitelj.email)
    _oddaj_s_priponkami(odjemalec, projektor, [("slika.png", PNG), ("porocilo.pdf", PDF)])

    with transakcija() as k:
        k.execute("SELECT id FROM prijava_tezave")
        id_prijave = k.fetchone()["id"]
        priponke = repo_prijave.priponke(k, id_prijave)
    assert [p["vrsta"] for p in priponke] == ["image/png", "application/pdf"]

    pot = f"/prijave/priponka/{priponke[0]['id']}"
    assert odjemalec.get(pot).data == PNG

    for drug, pricakovano in [(ucitelj2, 403), (skrbnik, 200)]:
        odjemalec.post("/odjava")
        prijavi(odjemalec, drug.email)
        assert odjemalec.get(pot).status_code == pricakovano


def test_nedovoljena_priponka_zavrne_celotno_prijavo(odjemalec, app, ucitelj, projektor):
    prijavi(odjemalec, ucitelj.email)
    # Končnica .png, vsebina pa ni slika – vrsta se preverja po vsebini.
    odgovor = _oddaj_s_priponkami(odjemalec, projektor, [("virus.png", b"MZ\x90\x00 to ni slika")])
    assert "ni JPEG, PNG ali PDF" in odgovor.get_data(as_text=True)
    assert _stevilo_prijav() == 0


def test_vec_kot_tri_priponke_so_zavrnjene(odjemalec, ucitelj, projektor):
    prijavi(odjemalec, ucitelj.email)
    odgovor = _oddaj_s_priponkami(odjemalec, projektor, [(f"{i}.png", PNG) for i in range(4)])
    assert "največ 3" in odgovor.get_data(as_text=True)
    assert _stevilo_prijav() == 0


def test_prevelika_priponka_je_zavrnjena(ucitelj, projektor):
    class Datoteka:
        filename = "velika.pdf"

        def read(self, n):
            return (PDF + b"x" * (6 * 1024 * 1024))[:n]

    with pytest.raises(PoslovnaNapaka, match="5 MiB"):
        storitev.oddaj(ucitelj, projektor["id"], None, "Naslov", "Opis", [Datoteka()])
    assert _stevilo_prijav() == 0
