"""Administracija: uporabniški računi (US-14)."""

from flask import Blueprint, flash, redirect, render_template, url_for

from .auth import zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecNovUporabnik
from .repositories import uporabniki as repo_uporabniki
from .services import uporabniki as storitev_uporabniki

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/uporabniki")
@zahteva_vlogo("administrator")
def uporabniki():
    with transakcija() as k:
        seznam = repo_uporabniki.vsi(k)
    return render_template("admin/uporabniki.html", uporabniki=seznam)


@bp.route("/uporabniki/nov", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def nov_uporabnik():
    obrazec = ObrazecNovUporabnik()
    if obrazec.validate_on_submit():
        try:
            storitev_uporabniki.ustvari(obrazec.ime.data, obrazec.priimek.data,
                                        obrazec.email.data, obrazec.geslo.data,
                                        obrazec.vloga.data)
            flash("Račun je ustvarjen. Začetno geslo posreduj uporabniku.", "uspeh")
            return redirect(url_for("admin.uporabniki"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/nov_uporabnik.html", obrazec=obrazec)
