"""Ukazi za ukazno vrstico.

    flask --app backend/app create-admin     # prvi administrator
"""

import click

from .napake import PoslovnaNapaka
from .services import uporabniki as storitev_uporabniki


@click.command("create-admin")
@click.option("--ime", prompt="Ime")
@click.option("--priimek", prompt="Priimek")
@click.option("--email", prompt="E-poštni naslov")
@click.password_option("--geslo", prompt="Geslo", confirmation_prompt="Ponovi geslo")
def ukaz_create_admin(ime, priimek, email, geslo):
    """Ustvari administratorski račun (geslo se vnese interaktivno)."""
    try:
        storitev_uporabniki.ustvari(ime, priimek, email, geslo, "administrator")
    except PoslovnaNapaka as e:
        raise click.ClickException(e.sporocilo) from e
    click.echo(f"Administrator {email.strip().lower()} je ustvarjen.")


def init_app(app):
    app.cli.add_command(ukaz_create_admin)
