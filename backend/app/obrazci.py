"""Obrazci (Flask-WTF).

Flask-WTF vsakemu obrazcu doda skrito polje csrf_token, ki ščiti pred
napadom CSRF (tuja stran ne more v imenu uporabnika oddati obrazca).

Filter _ocisti odstrani presledke na začetku in koncu, zato DataRequired
zavrne tudi vnos, ki vsebuje samo presledke.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    EmailField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, Regexp

OBLIKA_DATUMA_CASA = "%Y-%m-%dT%H:%M"
# Preprosto preverjanje oblike ime@domena.si (brez presledkov).
VZOREC_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _ocisti(vrednost):
    return vrednost.strip() if isinstance(vrednost, str) else vrednost


def _prazno_v_none(vrednost):
    """Prazno besedilo shrani kot NULL (za neobvezna polja, npr. opis)."""
    vrednost = _ocisti(vrednost)
    return vrednost or None


OBVEZNO = "To polje je obvezno."


class ObrazecPrazen(FlaskForm):
    """Obrazec brez polj – samo za CSRF zaščito gumbov (npr. »Prevzemi«)."""


class ObrazecPrijava(FlaskForm):
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO), Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov.")])
    geslo = PasswordField("Geslo", validators=[DataRequired(OBVEZNO)])
    potrdi = SubmitField("Prijava")


class ObrazecTermin(FlaskForm):
    zacetek = DateTimeLocalField("Začetek", format=OBLIKA_DATUMA_CASA,
                                 validators=[DataRequired("Vnesi datum in čas začetka.")])
    konec = DateTimeLocalField("Konec", format=OBLIKA_DATUMA_CASA,
                               validators=[DataRequired("Vnesi datum in čas konca.")])
    preveri = SubmitField("Preveri termin")
    potrdi = SubmitField("Potrdi rezervacijo")


class ObrazecPreklic(FlaskForm):
    razlog = TextAreaField("Razlog preklica", filters=[_prazno_v_none],
                           validators=[Optional(), Length(max=2000)])
    potrdi = SubmitField("Prekliči rezervacijo")


class ObrazecPrijavaTezave(FlaskForm):
    naslov = StringField("Naslov", filters=[_ocisti],
                         validators=[DataRequired(OBVEZNO), Length(max=150)])
    opis = TextAreaField("Opis težave", filters=[_ocisti],
                         validators=[DataRequired(OBVEZNO), Length(max=5000)])
    # Vrednost 0 pomeni »ni izbrano«.
    oprema_id = SelectField("Oprema", coerce=int, default=0)
    ucilnica_id = SelectField("Učilnica", coerce=int, default=0)
    priponke = MultipleFileField("Priponke (do 3 datoteke JPEG, PNG ali PDF, vsaka do 5 MiB)")
    potrdi = SubmitField("Oddaj prijavo")


class ObrazecResitev(FlaskForm):
    resitev = TextAreaField("Opis rešitve", filters=[_ocisti],
                            validators=[DataRequired("Pred zaključkom vnesi opis rešitve."),
                                        Length(max=5000)])
    potrdi = SubmitField("Zaključi kot rešeno")


class ObrazecPrerazporeditev(FlaskForm):
    skrbnik_id = SelectField("Novi odgovorni skrbnik", coerce=int)
    potrdi = SubmitField("Prerazporedi")


class ObrazecKomentar(FlaskForm):
    besedilo = TextAreaField("Komentar", filters=[_ocisti],
                             validators=[DataRequired(OBVEZNO), Length(max=5000)])
    potrdi = SubmitField("Dodaj komentar")


class ObrazecUporabnik(FlaskForm):
    ime = StringField("Ime", filters=[_ocisti], validators=[DataRequired(OBVEZNO), Length(max=100)])
    priimek = StringField("Priimek", filters=[_ocisti],
                          validators=[DataRequired(OBVEZNO), Length(max=100)])
    email = EmailField("E-poštni naslov", filters=[_ocisti],
                       validators=[DataRequired(OBVEZNO), Regexp(VZOREC_EMAIL, message="Neveljaven e-poštni naslov."),
                                   Length(max=254)])
    vloga = SelectField("Vloga", choices=[
        ("ucitelj", "Učitelj"),
        ("ikt_skrbnik", "IKT skrbnik"),
        ("administrator", "Administrator"),
    ])
    geslo = PasswordField("Geslo", validators=[Optional(), Length(min=8, max=200,
                          message="Geslo mora imeti vsaj 8 znakov.")])
    aktiven = BooleanField("Račun je aktiven", default=True)
    potrdi = SubmitField("Shrani")


class ObrazecUcilnica(FlaskForm):
    oznaka = StringField("Oznaka", filters=[_ocisti], validators=[DataRequired(OBVEZNO), Length(max=30)])
    naziv = StringField("Naziv", filters=[_ocisti], validators=[DataRequired(OBVEZNO), Length(max=100)])
    opis = TextAreaField("Opis", filters=[_prazno_v_none], validators=[Optional(), Length(max=2000)])
    potrdi = SubmitField("Shrani")


class ObrazecOprema(FlaskForm):
    naziv = StringField("Naziv", filters=[_ocisti], validators=[DataRequired(OBVEZNO), Length(max=150)])
    inventarna_stevilka = StringField("Inventarna številka", filters=[_ocisti],
                                      validators=[DataRequired(OBVEZNO), Length(max=50)])
    vrsta = StringField("Vrsta", filters=[_ocisti], validators=[DataRequired(OBVEZNO), Length(max=50)])
    opis = TextAreaField("Opis", filters=[_prazno_v_none], validators=[Optional(), Length(max=2000)])
    stanje = SelectField("Stanje", choices=[("uporabna", "Uporabna"), ("nedelujoca", "Nedelujoča")])
    ucilnica_id = SelectField("Lokacija (učilnica)", coerce=int)
    potrdi = SubmitField("Shrani")


class ObrazecObdobje(FlaskForm):
    # Obrazec za filtriranje (GET), zato brez CSRF.
    class Meta:
        csrf = False

    od = DateField("Od (vključno)", validators=[DataRequired(OBVEZNO)])
    do = DateField("Do (vključno)", validators=[DataRequired(OBVEZNO)])
    potrdi = SubmitField("Prikaži")
