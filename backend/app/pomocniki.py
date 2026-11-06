"""Manjše pomožne funkcije za poti."""

from flask import request, url_for


def je_lokalna_pot(pot):
    """Dovolimo samo poti znotraj aplikacije, npr. /rezervacije/moje.

    Tako napadalec ne more sestaviti povezave, ki bi uporabnika po prijavi
    preusmerila na tujo stran (t. i. "open redirect").
    """
    return bool(pot) and pot.startswith("/") and not pot.startswith("//") and "\\" not in pot


def pot_nazaj(privzeto, kljuc="naprej"):
    """Pot iz skritega polja obrazca (ali parametra URL) oziroma privzeta pot."""
    pot = request.form.get(kljuc) or request.args.get(kljuc)
    return pot if je_lokalna_pot(pot) else url_for(privzeto)
