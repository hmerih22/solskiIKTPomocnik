"""Ukazi za ukazno vrstico.

    flask --app backend/app create-admin     # prvi administrator (ADR-0005)
    flask --app backend/app demo-podatki     # testni podatki za preizkus aplikacije
"""

from datetime import timedelta

import click

from .cas import zdaj_utc
from .db import transakcija
from .napake import PoslovnaNapaka
from .repositories import oprema as repo_oprema
from .repositories import prijave as repo_prijave
from .repositories import rezervacije as repo_rezervacije
from .repositories import ucilnice as repo_ucilnice
from .repositories import uporabniki as repo_uporabniki
from .services import uporabniki as storitev_uporabniki


@click.command("create-admin")
@click.option("--ime", prompt="Ime")
@click.option("--priimek", prompt="Priimek")
@click.option("--email", prompt="E-poštni naslov")
@click.password_option("--geslo", prompt="Geslo", confirmation_prompt="Ponovi geslo")
def ukaz_create_admin(ime, priimek, email, geslo):
    """Ustvari administratorski račun (geslo se vnese interaktivno)."""
    try:
        storitev_uporabniki.ustvari(ime.strip(), priimek.strip(), email, geslo, "administrator")
    except PoslovnaNapaka as e:
        raise click.ClickException(e.sporocilo) from e
    click.echo(f"Administrator {email.strip().lower()} je ustvarjen.")


DEMO_GESLO = "demo1234"


@click.command("demo-podatki")
def ukaz_demo_podatki():
    """Napolni prazno bazo s primeri učilnic, opreme, uporabnikov in prijav.

    Vsi demo uporabniki imajo geslo demo1234. Ukaz je namenjen samo
    lokalnemu preizkusu – ne uporabljaj ga s pravimi šolskimi podatki.
    """
    with transakcija() as k:
        if repo_ucilnice.vse(k):
            raise click.ClickException("Baza že vsebuje učilnice – demo podatki niso dodani.")

    uporabniki = {}
    for ime, priimek, email, vloga in [
        ("Ana", "Admin", "admin@sola.si", "administrator"),
        ("Igor", "Skrbnik", "skrbnik@sola.si", "ikt_skrbnik"),
        ("Iva", "Tehnik", "skrbnik2@sola.si", "ikt_skrbnik"),
        ("Uroš", "Učitelj", "ucitelj@sola.si", "ucitelj"),
        ("Maja", "Novak", "ucitelj2@sola.si", "ucitelj"),
    ]:
        with transakcija() as k:
            obstojeci = repo_uporabniki.najdi_po_emailu(k, email)
        if obstojeci:
            uporabniki[email] = obstojeci["id"]
        else:
            uporabniki[email] = storitev_uporabniki.ustvari(ime, priimek, email, DEMO_GESLO, vloga)

    zdaj = zdaj_utc().replace(minute=0, second=0, microsecond=0)
    with transakcija() as k:
        u12 = repo_ucilnice.ustvari(k, "12", "Računalniška učilnica", "Prvo nadstropje, 24 računalnikov")
        u21 = repo_ucilnice.ustvari(k, "21", "Učilnica za matematiko", None)
        kab = repo_ucilnice.ustvari(k, "KAB-IKT", "Kabinet IKT", "Skladišče prenosne opreme")

        proj1 = repo_oprema.ustvari(k, "Projektor 1", "INV-0001", "projektor", "Epson, HDMI", "uporabna", u12)
        proj2 = repo_oprema.ustvari(k, "Projektor 2", "INV-0002", "projektor", None, "nedelujoca", u21)
        tabl = repo_oprema.ustvari(k, "Komplet 15 tablic", "INV-0100", "komplet tablic",
                                   "15 tablic v kovčku s polnilnikom", "uporabna", kab)
        pren = repo_oprema.ustvari(k, "Prenosnik Dell 3", "INV-0203", "prenosnik", None, "uporabna", kab)
        repo_oprema.ustvari(k, "Pametna tabla", "INV-0300", "pametna tabla", None, "uporabna", u21)

        ucitelj = uporabniki["ucitelj@sola.si"]
        ucitelj2 = uporabniki["ucitelj2@sola.si"]
        skrbnik = uporabniki["skrbnik@sola.si"]

        jutri = zdaj + timedelta(days=1)
        repo_rezervacije.ustvari(k, ucitelj, proj1, jutri, jutri + timedelta(hours=1))
        repo_rezervacije.ustvari(k, ucitelj2, proj1, jutri + timedelta(hours=1), jutri + timedelta(hours=2))
        repo_rezervacije.ustvari(k, ucitelj, tabl, jutri + timedelta(days=1), jutri + timedelta(days=1, hours=2))
        # Prihodnja rezervacija nedelujoče opreme – prikaže se opozorilo (US-07).
        repo_rezervacije.ustvari(k, ucitelj2, proj2, jutri + timedelta(days=2), jutri + timedelta(days=2, hours=1))
        # Pretekla rezervacija s prevzemom brez vračila – zamuda (US-08).
        vceraj = zdaj - timedelta(days=1)
        id_pretekle = repo_rezervacije.ustvari(k, ucitelj, pren, vceraj, vceraj + timedelta(hours=2))
        repo_rezervacije.zabelezi_prevzem(k, id_pretekle, vceraj)

        repo_prijave.ustvari(k, ucitelj, None, u12, "Ni interneta", "V učilnici 12 ne deluje Wi-Fi.")
        id_p2 = repo_prijave.ustvari(k, ucitelj2, proj2, u21, "Projektor ne prižge",
                                     "Lučka utripa rdeče, slike ni.")
        repo_prijave.prevzemi(k, id_p2, skrbnik, zdaj - timedelta(hours=3))
        repo_prijave.dodaj_komentar(k, id_p2, skrbnik, "Ali je projektor priklopljen na elektriko?")
        repo_prijave.dodaj_komentar(k, id_p2, ucitelj2, "Da, kabel je priklopljen.")
        id_p3 = repo_prijave.ustvari(k, ucitelj, tabl, None, "Tablica 7 se ne polni",
                                     "Ena od tablic v kompletu se ne polni.")
        repo_prijave.prevzemi(k, id_p3, skrbnik, zdaj - timedelta(hours=2))
        repo_prijave.zakljuci(k, id_p3, "Zamenjan polnilni kabel.", zdaj - timedelta(hours=1))

    click.echo("Demo podatki so dodani. Prijava (geslo za vse: demo1234):")
    for email in uporabniki:
        click.echo(f"  {email}")


def init_app(app):
    app.cli.add_command(ukaz_create_admin)
    app.cli.add_command(ukaz_demo_podatki)
