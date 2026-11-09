"""Administracija: uporabniški računi (US-14), učilnice in oprema (US-15)."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from .auth import zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecNovUporabnik, ObrazecUcilnica, ObrazecUrejanjeUporabnika
from .repositories import ucilnice as repo_ucilnice
from .repositories import uporabniki as repo_uporabniki
from .services import evidence as storitev_evidence
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


@bp.route("/uporabniki/<int:id_uporabnika>", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def uredi_uporabnika(id_uporabnika):
    with transakcija() as k:
        uporabnik = repo_uporabniki.najdi(k, id_uporabnika)
    if uporabnik is None:
        abort(404)

    obrazec = ObrazecUrejanjeUporabnika(data=uporabnik)
    if obrazec.validate_on_submit():
        try:
            storitev_uporabniki.posodobi(current_user, id_uporabnika, obrazec.ime.data,
                                         obrazec.priimek.data, obrazec.email.data,
                                         obrazec.vloga.data, obrazec.aktiven.data)
            flash("Podatki uporabnika so shranjeni.", "uspeh")
            return redirect(url_for("admin.uporabniki"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/uredi_uporabnika.html", obrazec=obrazec, uporabnik=uporabnik)


# --- Učilnice (US-15) ---------------------------------------------------------

@bp.get("/ucilnice")
@zahteva_vlogo("administrator")
def ucilnice():
    with transakcija() as k:
        seznam = repo_ucilnice.vse(k)
    return render_template("admin/ucilnice.html", ucilnice=seznam)


@bp.route("/ucilnice/nova", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def nova_ucilnica():
    obrazec = ObrazecUcilnica()
    if obrazec.validate_on_submit():
        try:
            storitev_evidence.dodaj_ucilnico(current_user, obrazec.oznaka.data,
                                             obrazec.naziv.data, obrazec.opis.data)
            flash("Učilnica je dodana.", "uspeh")
            return redirect(url_for("admin.ucilnice"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/ucilnica.html", obrazec=obrazec, ucilnica=None)


@bp.route("/ucilnice/<int:id_ucilnice>", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def uredi_ucilnico(id_ucilnice):
    with transakcija() as k:
        ucilnica = repo_ucilnice.najdi(k, id_ucilnice)
    if ucilnica is None:
        abort(404)

    obrazec = ObrazecUcilnica(data=ucilnica)
    # Oznake ni mogoče spreminjati: vedno uporabimo shranjeno vrednost.
    obrazec.oznaka.data = ucilnica["oznaka"]
    if obrazec.validate_on_submit():
        try:
            storitev_evidence.uredi_ucilnico(current_user, id_ucilnice, obrazec.naziv.data,
                                             obrazec.opis.data)
            flash("Učilnica je shranjena.", "uspeh")
            return redirect(url_for("admin.ucilnice"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/ucilnica.html", obrazec=obrazec, ucilnica=ucilnica)
