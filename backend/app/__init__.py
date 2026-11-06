"""Šolski IKT pomočnik – Flask aplikacija.

Funkcija create_app ustvari in nastavi aplikacijo (vzorec "application factory").
Zažene se iz korenske mape projekta z ukazom:

    flask --app backend/app run --debug
"""

from pathlib import Path

from flask import Flask, render_template

from .config import nalozi_nastavitve

# Predloge in statične datoteke so v mapi frontend/, ne znotraj paketa app,
# zato Flasku povemo, kje jih najde.
KORENSKA_MAPA = Path(__file__).resolve().parents[2]
MAPA_PREDLOG = KORENSKA_MAPA / "frontend" / "templates"
MAPA_STATICNIH = KORENSKA_MAPA / "frontend" / "static"


def create_app(test_config=None):
    """Ustvari Flask aplikacijo.

    test_config: slovar nastavitev za teste. Če je podan, se .env ne bere,
    tako da testi ne potrebujejo prave datoteke .env.
    """
    app = Flask(
        __name__,
        template_folder=str(MAPA_PREDLOG),
        static_folder=str(MAPA_STATICNIH),
    )

    if test_config is None:
        app.config.update(nalozi_nastavitve())
    else:
        app.config.update(test_config)

    @app.get("/")
    def domov():
        return render_template("index.html")

    return app
