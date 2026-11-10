"""Pregled opreme (US-01) in sprememba uporabnosti (US-07)."""

from flask import Blueprint, abort, flash, redirect, render_template, request
from flask_login import current_user, login_required

from .auth import zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecPrazen
from .pomocniki import pot_nazaj
from .repositories import oprema as repo_oprema
from .services import evidence as storitev_evidence

bp = Blueprint("oprema", __name__, url_prefix="/oprema")


@bp.get("/")
@login_required
def seznam():
    """Vsa oprema, tudi nedelujoča (ta ostane vidna z oznako)."""
    with transakcija() as k:
        oprema = repo_oprema.vsa(k)
    return render_template("oprema/seznam.html", oprema=oprema, obrazec=ObrazecPrazen())


@bp.post("/<int:id_opreme>/stanje")
@zahteva_vlogo("ikt_skrbnik")
def spremeni_stanje(id_opreme):
    if not ObrazecPrazen().validate_on_submit():
        abort(400)
    stanje = request.form.get("stanje")
    try:
        storitev_evidence.spremeni_stanje_opreme(current_user, id_opreme, stanje)
    except PoslovnaNapaka as e:
        flash(e.sporocilo, "napaka")
    else:
        if stanje == "nedelujoca":
            flash("Oprema je označena kot nedelujoča. Nove rezervacije niso več mogoče.", "uspeh")
        else:
            flash("Oprema je ponovno označena kot uporabna.", "uspeh")
    # Nazaj na stran, s katere je prišla zahteva (seznam opreme ali prijava).
    return redirect(pot_nazaj("oprema.seznam"))
