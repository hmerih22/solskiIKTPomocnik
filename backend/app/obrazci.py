"""Obrazci (Flask-WTF).

Flask-WTF vsakemu obrazcu doda skrito polje csrf_token, ki ščiti pred
napadom CSRF (tuja stran ne more v imenu uporabnika oddati obrazca).

Filter _ocisti odstrani presledke na začetku in koncu, zato DataRequired
zavrne tudi vnos, ki vsebuje samo presledke.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateTimeLocalField, EmailField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from .vloge import NAZIVI_VLOG

# Preprosto preverjanje oblike ime@domena.si (brez presledkov).
VZOREC_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
# Oblika vnosa <input type="datetime-local">, npr. 2026-11-10T09:00.
OBLIKA_DATUMA_CASA = "%Y-%m-%dT%H:%M"
OBVEZNO = "To polje je obvezno."


def _ocisti(vrednost):
    return vrednost.strip() if isinstance(vrednost, str) else vrednost


class ObrazecPrijava(FlaskForm):
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO),
                                   Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov.")])
    geslo = PasswordField("Geslo", validators=[DataRequired(OBVEZNO)])
    potrdi = SubmitField("Prijava")


class ObrazecNovUporabnik(FlaskForm):
    ime = StringField("Ime", filters=[_ocisti],
                      validators=[DataRequired(OBVEZNO), Length(max=100)])
    priimek = StringField("Priimek", filters=[_ocisti],
                          validators=[DataRequired(OBVEZNO), Length(max=100)])
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO), Length(max=254),
                                   Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov.")])
    geslo = PasswordField("Začetno geslo",
                          validators=[DataRequired(OBVEZNO),
                                      Length(min=8, message="Geslo mora imeti vsaj 8 znakov.")])
    # Seznam vlog je zaprt: vrednost, ki ni na seznamu, obrazec zavrne.
    vloga = SelectField("Vloga", choices=list(NAZIVI_VLOG.items()), default="ucitelj")
    potrdi = SubmitField("Ustvari račun")


class ObrazecUrejanjeUporabnika(FlaskForm):
    ime = StringField("Ime", filters=[_ocisti],
                      validators=[DataRequired(OBVEZNO), Length(max=100)])
    priimek = StringField("Priimek", filters=[_ocisti],
                          validators=[DataRequired(OBVEZNO), Length(max=100)])
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO), Length(max=254),
                                   Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov.")])
    vloga = SelectField("Vloga", choices=list(NAZIVI_VLOG.items()))
    aktiven = BooleanField("Račun je aktiven")
    potrdi = SubmitField("Shrani spremembe")


class ObrazecUcilnica(FlaskForm):
    oznaka = StringField("Oznaka", filters=[_ocisti],
                         validators=[DataRequired(OBVEZNO), Length(max=30)])
    naziv = StringField("Naziv", filters=[_ocisti],
                        validators=[DataRequired(OBVEZNO), Length(max=100)])
    opis = TextAreaField("Opis", filters=[_ocisti], validators=[Optional(), Length(max=2000)])
    potrdi = SubmitField("Shrani")


class ObrazecOprema(FlaskForm):
    naziv = StringField("Naziv", filters=[_ocisti],
                        validators=[DataRequired(OBVEZNO), Length(max=150)])
    inventarna_stevilka = StringField("Inventarna številka", filters=[_ocisti],
                                      validators=[DataRequired(OBVEZNO), Length(max=50)])
    vrsta = StringField("Vrsta", filters=[_ocisti],
                        validators=[DataRequired(OBVEZNO), Length(max=50)])
    opis = TextAreaField("Opis", filters=[_ocisti], validators=[Optional(), Length(max=2000)])
    stanje = SelectField("Stanje", choices=[("uporabna", "Uporabna"), ("nedelujoca", "Nedelujoča")])
    # Izbire (učilnice) se nastavijo v poti, ker prihajajo iz baze.
    ucilnica_id = SelectField("Lokacija (učilnica)", coerce=int)
    potrdi = SubmitField("Shrani")


class ObrazecTermin(FlaskForm):
    """Termin rezervacije v lokalnem času (Europe/Ljubljana)."""

    zacetek = DateTimeLocalField("Začetek", format=OBLIKA_DATUMA_CASA,
                                 validators=[DataRequired("Vnesi datum in čas začetka.")])
    konec = DateTimeLocalField("Konec", format=OBLIKA_DATUMA_CASA,
                               validators=[DataRequired("Vnesi datum in čas konca.")])
    preveri = SubmitField("Preveri termin")
