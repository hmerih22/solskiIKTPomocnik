"""Rezervacije opreme: preverjanje termina (US-02) in rezervacija (US-03)."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from .cas import v_utc, zdaj_utc
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecTermin
from .repositories import oprema as repo_oprema
from .repositories import rezervacije as repo_rezervacije
from .services import rezervacije as storitev

bp = Blueprint("rezervacije", __name__, url_prefix="/rezervacije")


@bp.route("/nova/<int:id_opreme>", methods=["GET", "POST"])
@login_required
def nova(id_opreme):
    """Izbira termina z gumboma »Preveri termin« in »Potrdi rezervacijo« (WF-02).

    Ob potrditvi storitev termin preveri še enkrat (pod zaklepom), saj ga je
    lahko med preverjanjem in potrditvijo zasedel nekdo drug.
    """
    with transakcija() as k:
        oprema = repo_oprema.najdi(k, id_opreme)
    if oprema is None:
        abort(404)

    obrazec = ObrazecTermin()
    rezultat = None
    if obrazec.validate_on_submit():
        zacetek = v_utc(obrazec.zacetek.data)
        konec = v_utc(obrazec.konec.data)
        try:
            if obrazec.potrdi.data:
                storitev.ustvari(current_user, id_opreme, zacetek, konec)
                flash("Rezervacija je potrjena.", "uspeh")
                return redirect(url_for("rezervacije.nova", id_opreme=id_opreme))
            rezultat = storitev.preveri_razpolozljivost(id_opreme, zacetek, konec)
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")

    with transakcija() as k:
        zasedeni = repo_rezervacije.zasedeni_termini(k, id_opreme, zdaj_utc())
    return render_template("rezervacije/nova.html", oprema=oprema, obrazec=obrazec,
                           rezultat=rezultat, zasedeni=zasedeni)
