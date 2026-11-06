"""Administracija: uporabniki (US-14), učilnice in oprema (US-15),
evidenca obvestil (F11)."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from .auth import NAZIVI_VLOG, zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecOprema, ObrazecUcilnica, ObrazecUporabnik
from .repositories import obvestila as repo_obvestila
from .repositories import oprema as repo_oprema
from .repositories import ucilnice as repo_ucilnice
from .repositories import uporabniki as repo_uporabniki
from .services import oprema as storitev_oprema
from .services import uporabniki as storitev_uporabniki

bp = Blueprint("admin", __name__, url_prefix="/admin")


# --- Uporabniki --------------------------------------------------------------

@bp.get("/uporabniki")
@zahteva_vlogo("administrator")
def uporabniki():
    with transakcija() as k:
        seznam = repo_uporabniki.vsi(k)
    return render_template("admin/uporabniki.html", uporabniki=seznam, vloge=NAZIVI_VLOG)


@bp.route("/uporabniki/nov", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def nov_uporabnik():
    obrazec = ObrazecUporabnik()
    if obrazec.validate_on_submit():
        if not obrazec.geslo.data:
            flash("Za nov račun vnesi začetno geslo.", "napaka")
        else:
            try:
                storitev_uporabniki.ustvari_kot_administrator(
                    current_user, obrazec.ime.data, obrazec.priimek.data, obrazec.email.data,
                    obrazec.geslo.data, obrazec.vloga.data,
                )
                flash("Račun je ustvarjen. Začetno geslo posreduj uporabniku.", "uspeh")
                return redirect(url_for("admin.uporabniki"))
            except PoslovnaNapaka as e:
                flash(e.sporocilo, "napaka")
    return render_template("admin/uporabnik.html", obrazec=obrazec, nov=True)


@bp.route("/uporabniki/<int:id_uporabnika>", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def uredi_uporabnika(id_uporabnika):
    with transakcija() as k:
        uporabnik = repo_uporabniki.najdi(k, id_uporabnika)
    if uporabnik is None:
        abort(404)

    obrazec = ObrazecUporabnik(data=uporabnik)
    if obrazec.validate_on_submit():
        try:
            storitev_uporabniki.posodobi(
                current_user, id_uporabnika, obrazec.ime.data, obrazec.priimek.data,
                obrazec.email.data, obrazec.vloga.data, obrazec.aktiven.data, obrazec.geslo.data,
            )
            flash("Podatki uporabnika so shranjeni.", "uspeh")
            return redirect(url_for("admin.uporabniki"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/uporabnik.html", obrazec=obrazec, nov=False,
                           uporabnik=uporabnik)


# --- Učilnice ----------------------------------------------------------------

@bp.get("/ucilnice")
@zahteva_vlogo("administrator")
def ucilnice():
    with transakcija() as k:
        seznam = repo_ucilnice.vse(k)
    return render_template("admin/ucilnice.html", ucilnice=seznam)


@bp.route("/ucilnice/nova", methods=["GET", "POST"], defaults={"id_ucilnice": None})
@bp.route("/ucilnice/<int:id_ucilnice>", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def uredi_ucilnico(id_ucilnice):
    ucilnica = None
    if id_ucilnice is not None:
        with transakcija() as k:
            ucilnica = repo_ucilnice.najdi(k, id_ucilnice)
        if ucilnica is None:
            abort(404)

    obrazec = ObrazecUcilnica(data=ucilnica)
    if obrazec.validate_on_submit():
        try:
            storitev_oprema.shrani_ucilnico(current_user, id_ucilnice, obrazec.oznaka.data,
                                            obrazec.naziv.data, obrazec.opis.data)
            flash("Učilnica je shranjena.", "uspeh")
            return redirect(url_for("admin.ucilnice"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/ucilnica.html", obrazec=obrazec, ucilnica=ucilnica)


# --- Oprema ------------------------------------------------------------------

@bp.route("/oprema/nova", methods=["GET", "POST"], defaults={"id_opreme": None})
@bp.route("/oprema/<int:id_opreme>", methods=["GET", "POST"])
@zahteva_vlogo("administrator")
def uredi_opremo(id_opreme):
    with transakcija() as k:
        oprema = repo_oprema.najdi(k, id_opreme) if id_opreme is not None else None
        ucilnice_seznam = repo_ucilnice.vse(k)
    if id_opreme is not None and oprema is None:
        abort(404)
    if not ucilnice_seznam:
        flash("Najprej dodaj vsaj eno učilnico (lokacijo opreme).", "opozorilo")
        return redirect(url_for("admin.uredi_ucilnico"))

    obrazec = ObrazecOprema(data=oprema)
    obrazec.ucilnica_id.choices = [(u["id"], f"{u['oznaka']} – {u['naziv']}") for u in ucilnice_seznam]
    if obrazec.validate_on_submit():
        try:
            storitev_oprema.shrani_opremo(
                current_user, id_opreme, obrazec.naziv.data, obrazec.inventarna_stevilka.data,
                obrazec.vrsta.data, obrazec.opis.data, obrazec.stanje.data,
                obrazec.ucilnica_id.data,
            )
            flash("Oprema je shranjena.", "uspeh")
            return redirect(url_for("oprema.seznam"))
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return render_template("admin/oprema.html", obrazec=obrazec, oprema=oprema)


# --- Obvestila (F11) ---------------------------------------------------------

@bp.get("/obvestila")
@zahteva_vlogo("administrator")
def obvestila():
    with transakcija() as k:
        seznam = repo_obvestila.zadnja(k)
    return render_template("admin/obvestila.html", obvestila=seznam)
