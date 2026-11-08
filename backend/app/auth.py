"""Prijava, odjava, nalaganje uporabnika in preverjanje vlog (US-13).

V seji je shranjen samo id uporabnika. Ob vsaki zahtevi Flask-Login pokliče
nalozi_uporabnika(), ki uporabnika ponovno prebere iz baze. Zato
deaktivacija ali sprememba vloge učinkuje že pri naslednji zahtevi.
"""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from .db import transakcija
from .obrazci import ObrazecPrijava
from .pomocniki import pot_nazaj
from .repositories import uporabniki as repo_uporabniki

bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.prijava"
login_manager.login_message = "Za dostop do te strani se prijavi."
login_manager.login_message_category = "opozorilo"

# Vloge od najmanj do največ pravic. Višja vloga ima vse pravice nižjih.
VLOGE = ["ucitelj", "ikt_skrbnik", "administrator"]
NAZIVI_VLOG = {
    "ucitelj": "Učitelj",
    "ikt_skrbnik": "IKT skrbnik",
    "administrator": "Administrator",
}


class Uporabnik(UserMixin):
    """Prijavljeni uporabnik (ovoj okoli vrstice iz tabele uporabnik)."""

    def __init__(self, vrstica):
        self.id = vrstica["id"]
        self.ime = vrstica["ime"]
        self.priimek = vrstica["priimek"]
        self.email = vrstica["email"]
        self.vloga = vrstica["vloga"]
        self.aktiven = bool(vrstica["aktiven"])

    @property
    def is_active(self):
        # Flask-Login neaktivnega uporabnika ne prijavi.
        return self.aktiven

    @property
    def polno_ime(self):
        return f"{self.ime} {self.priimek}"

    def ima_vlogo(self, najmanjsa_vloga):
        """Ali ima uporabnik vsaj podano vlogo (npr. administrator je tudi skrbnik)."""
        return VLOGE.index(self.vloga) >= VLOGE.index(najmanjsa_vloga)

    @property
    def je_skrbnik(self):
        return self.ima_vlogo("ikt_skrbnik")

    @property
    def je_administrator(self):
        return self.ima_vlogo("administrator")


@login_manager.user_loader
def nalozi_uporabnika(id_uporabnika):
    with transakcija() as k:
        vrstica = repo_uporabniki.najdi(k, int(id_uporabnika))
    if vrstica is None or not vrstica["aktiven"]:
        # Izbrisan ali deaktiviran račun: seja ni več veljavna.
        return None
    return Uporabnik(vrstica)


def zahteva_vlogo(najmanjsa_vloga):
    """Dekorator: pot je dostopna samo prijavljenim z vsaj podano vlogo.

    Neprijavljeni uporabnik je preusmerjen na prijavo, prijavljeni brez
    ustrezne vloge pa dobi odgovor 403 (prepovedano). Preverjanje se izvede
    na zaledju, zato ga ni mogoče obiti z neposredno zahtevo.

        @bp.get("/uporabniki")
        @zahteva_vlogo("administrator")
        def uporabniki(): ...
    """
    if najmanjsa_vloga not in VLOGE:
        raise ValueError(f"Neznana vloga: {najmanjsa_vloga}")

    def dekorator(funkcija):
        @wraps(funkcija)
        @login_required
        def ovoj(*args, **kwargs):
            if not current_user.ima_vlogo(najmanjsa_vloga):
                abort(403)
            return funkcija(*args, **kwargs)

        return ovoj

    return dekorator


@bp.route("/prijava", methods=["GET", "POST"])
def prijava():
    if current_user.is_authenticated:
        return redirect(url_for("domov"))

    obrazec = ObrazecPrijava()
    if obrazec.validate_on_submit():
        with transakcija() as k:
            vrstica = repo_uporabniki.najdi_po_emailu(k, obrazec.email.data.lower())

        # Isto sporočilo za napačen e-naslov in napačno geslo: napadalec
        # tako ne izve, kateri e-naslovi obstajajo.
        if vrstica is None or not check_password_hash(vrstica["geslo_hash"], obrazec.geslo.data):
            flash("Napačen e-poštni naslov ali geslo.", "napaka")
        elif not vrstica["aktiven"]:
            flash("Račun je deaktiviran. Obrni se na administratorja.", "napaka")
        else:
            login_user(Uporabnik(vrstica))
            flash(f"Pozdravljen, {vrstica['ime']}!", "uspeh")
            # Flask-Login doda ?next=/stran, s katere je bil uporabnik preusmerjen.
            return redirect(pot_nazaj("domov", kljuc="next"))

    return render_template("auth/prijava.html", obrazec=obrazec)


@bp.post("/odjava")
@login_required
def odjava():
    logout_user()
    flash("Odjavljen si.", "uspeh")
    return redirect(url_for("auth.prijava"))
