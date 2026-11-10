"""Šolski IKT pomočnik – Flask aplikacija.

Funkcija create_app ustvari in nastavi aplikacijo (vzorec "application factory").
Zažene se iz korenske mape projekta z ukazom:

    flask --app backend/app run --debug
"""

from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import login_required
from flask_wtf.csrf import CSRFProtect

from . import admin, auth, cli, db, oprema, prijave, rezervacije
from .cas import oblikuj
from .config import nalozi_nastavitve
from .napake import Prepovedano
from .services.prijave import STATUSI as STATUSI_PRIJAV

# Predloge in statične datoteke so v mapi frontend/, ne znotraj paketa app,
# zato Flasku povemo, kje jih najde.
KORENSKA_MAPA = Path(__file__).resolve().parents[2]
MAPA_PREDLOG = KORENSKA_MAPA / "frontend" / "templates"
MAPA_STATICNIH = KORENSKA_MAPA / "frontend" / "static"

# Zaščita CSRF za vse POST zahteve (tudi gumb za odjavo).
csrf = CSRFProtect()


def create_app(test_config=None):
    """Ustvari Flask aplikacijo.

    test_config: slovar nastavitev za teste. Če je podan, se .env ne bere,
    tako da testi ne potrebujejo prave datoteke .env.
    """
    app = Flask(
        __name__,
        template_folder=str(MAPA_PREDLOG),
        static_folder=str(MAPA_STATICNIH),
        instance_path=str(KORENSKA_MAPA / "instance"),
    )

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config is None:
        app.config.update(nalozi_nastavitve())
    else:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    auth.login_manager.init_app(app)
    cli.init_app(app)
    for modul in (auth, oprema, rezervacije, prijave, admin):
        app.register_blueprint(modul.bp)

    @app.get("/")
    @login_required
    def domov():
        return render_template("index.html")

    @app.get("/zdravje")
    def zdravje():
        return {"stanje": "ok"}

    _registriraj_predloge(app)
    _registriraj_napake(app)
    return app


def _registriraj_predloge(app):
    """Spremenljivke, ki so na voljo v vseh Jinja predlogah."""

    def ima_pot(ime):
        """Ali pot obstaja. Povezave na strani, ki še niso narejene, se ne prikažejo."""
        return ime in app.view_functions

    # {{ rezervacija.zacetek | cas }} prikaže UTC iz baze v lokalnem času.
    app.add_template_filter(oblikuj, "cas")

    @app.context_processor
    def skupne_spremenljivke():
        return {"nazivi_vlog": auth.NAZIVI_VLOG, "ima_pot": ima_pot,
                "statusi_prijav": STATUSI_PRIJAV}


def _registriraj_napake(app):
    @app.errorhandler(400)
    def slaba_zahteva(_napaka):
        return render_template("napaka.html", koda=400,
                               sporocilo="Zahteva ni veljavna. Osveži stran in poskusi znova."), 400

    @app.errorhandler(403)
    def prepovedano(_napaka):
        return render_template("napaka.html", koda=403,
                               sporocilo="Za to stran nimaš pravic."), 403

    @app.errorhandler(Prepovedano)
    def prepovedano_v_storitvi(_napaka):
        # Storitev je zavrnila operacijo zaradi pravic: enako kot 403.
        return prepovedano(_napaka)

    @app.errorhandler(404)
    def ni_najdeno(_napaka):
        return render_template("napaka.html", koda=404, sporocilo="Strani ni mogoče najti."), 404

    @app.route("/favicon.ico")
    def favicon():
        return redirect(url_for("static", filename="favicon.svg"))
