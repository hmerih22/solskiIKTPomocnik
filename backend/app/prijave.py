"""Prijave težav: oddaja (US-05)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecPrijavaTezave
from .repositories import oprema as repo_oprema
from .repositories import ucilnice as repo_ucilnice
from .services import prijave as storitev

bp = Blueprint("prijave", __name__, url_prefix="/prijave")


@bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    obrazec = ObrazecPrijavaTezave()
    with transakcija() as k:
        oprema = repo_oprema.vsa(k)
        ucilnice = repo_ucilnice.vse(k)
    obrazec.oprema_id.choices = [(0, "— brez opreme —")] + [
        (o["id"], f"{o['naziv']} ({o['inventarna_stevilka']})") for o in oprema
    ]
    obrazec.ucilnica_id.choices = [(0, "— brez učilnice —")] + [
        (u["id"], f"{u['oznaka']} – {u['naziv']}") for u in ucilnice
    ]

    if request.method == "GET":
        # Predizpolnitev, ko uporabnik pride s seznama opreme (»Prijavi težavo«).
        obrazec.oprema_id.data = request.args.get("oprema_id", 0, type=int)

    if obrazec.validate_on_submit():
        try:
            storitev.oddaj(current_user, obrazec.oprema_id.data, obrazec.ucilnica_id.data,
                           obrazec.naslov.data, obrazec.opis.data)
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
        else:
            flash("Prijava je oddana. IKT skrbnik jo bo prevzel v obravnavo.", "uspeh")
            return redirect(url_for("domov"))

    return render_template("prijave/nova.html", obrazec=obrazec)
