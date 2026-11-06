"""Pregled opreme (US-01) in sprememba uporabnosti (US-07)."""

from flask import Blueprint, abort, flash, redirect, render_template, request
from flask_login import current_user, login_required

from .auth import zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecPrazen
from .pomocniki import pot_nazaj
from .repositories import oprema as repo_oprema
from .services import oprema as storitev_oprema

bp = Blueprint("oprema", __name__, url_prefix="/oprema")


@bp.get("/")
@login_required
def seznam():
    with transakcija() as k:
        oprema = repo_oprema.vsa(k)
    return render_template("oprema/seznam.html", oprema=oprema, obrazec=ObrazecPrazen())


@bp.post("/<int:id_opreme>/stanje")
@zahteva_vlogo("ikt_skrbnik")
def spremeni_stanje(id_opreme):
    obrazec = ObrazecPrazen()
    if not obrazec.validate_on_submit():
        abort(400)

    stanje = request.form.get("stanje")
    try:
        prihodnje = storitev_oprema.spremeni_stanje(current_user, id_opreme, stanje)
    except PoslovnaNapaka as e:
        flash(e.sporocilo, "napaka")
    else:
        if stanje == "nedelujoca":
            flash("Oprema je označena kot nedelujoča. Nove rezervacije niso več mogoče.", "uspeh")
            if prihodnje:
                flash(
                    f"Pozor: oprema ima {prihodnje} prihodnjih rezervacij. Ostanejo v evidenci "
                    "z opozorilom; po potrebi jih prekliči z razlogom.",
                    "opozorilo",
                )
        else:
            flash("Oprema je ponovno označena kot uporabna.", "uspeh")

    # Vrnemo se na stran, s katere je prišla zahteva (seznam ali prijava).
    return redirect(pot_nazaj("oprema.seznam"))
