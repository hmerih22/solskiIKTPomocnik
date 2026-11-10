"""Prijave težav: oddaja in pregled (US-05)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecPrijavaTezave
from .repositories import oprema as repo_oprema
from .repositories import prijave as repo_prijave
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
            id_prijave = storitev.oddaj(current_user, obrazec.oprema_id.data, obrazec.ucilnica_id.data,
                           obrazec.naslov.data, obrazec.opis.data)
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
        else:
            flash("Prijava je oddana. IKT skrbnik jo bo prevzel v obravnavo.", "uspeh")
            return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave))

    return render_template("prijave/nova.html", obrazec=obrazec)


def _najdi_ali_404(k, id_prijave):
    prijava = repo_prijave.najdi(k, id_prijave)
    if prijava is None:
        abort(404)
    if not storitev.lahko_vidi(current_user, prijava):
        # Učitelj ne sme brati tuje prijave (US-05).
        abort(403)
    return prijava


@bp.get("/moje")
@login_required
def moje():
    with transakcija() as k:
        prijave = repo_prijave.za_prijavitelja(k, current_user.id)
    return render_template("prijave/seznam.html", prijave=prijave, naslov="Moje prijave",
                           vse=False, filter_status=None)


@bp.get("/<int:id_prijave>")
@login_required
def podrobnosti(id_prijave):
    with transakcija() as k:
        prijava = _najdi_ali_404(k, id_prijave)
    return render_template("prijave/podrobnosti.html", prijava=prijava)
