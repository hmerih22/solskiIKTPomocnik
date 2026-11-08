"""Šolski IKT pomočnik – Flask aplikacija.

Funkcija create_app ustvari in nastavi aplikacijo (vzorec "application factory").
Zažene se iz korenske mape projekta z ukazom:

    flask --app backend/app run --debug
"""

from pathlib import Path

from flask import Flask
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFProtect

from . import auth, db
from .config import nalozi_nastavitve

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
    app.register_blueprint(auth.bp)

    @app.get("/")
    @login_required
    def domov():
        return f"Pozdravljen, {current_user.polno_ime}!"

    @app.get("/zdravje")
    def zdravje():
        return {"stanje": "ok"}

    return app
