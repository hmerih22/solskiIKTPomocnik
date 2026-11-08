"""Obrazci (Flask-WTF).

Flask-WTF vsakemu obrazcu doda skrito polje csrf_token, ki ščiti pred
napadom CSRF (tuja stran ne more v imenu uporabnika oddati obrazca).

Filter _ocisti odstrani presledke na začetku in koncu, zato DataRequired
zavrne tudi vnos, ki vsebuje samo presledke.
"""

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Regexp

# Preprosto preverjanje oblike ime@domena.si (brez presledkov).
VZOREC_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
OBVEZNO = "To polje je obvezno."


def _ocisti(vrednost):
    return vrednost.strip() if isinstance(vrednost, str) else vrednost


class ObrazecPrijava(FlaskForm):
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO),
                                   Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov.")])
    geslo = PasswordField("Geslo", validators=[DataRequired(OBVEZNO)])
    potrdi = SubmitField("Prijava")
