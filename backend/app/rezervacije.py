"""Rezervacije opreme: preverjanje termina (US-02)."""

from flask import Blueprint, abort, flash, render_template
from flask_login import login_required

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
    """Izbira termina in gumb »Preveri termin« (zaslon WF-02)."""
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
            rezultat = storitev.preveri_razpolozljivost(id_opreme, zacetek, konec)
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")

    with transakcija() as k:
        zasedeni = repo_rezervacije.zasedeni_termini(k, id_opreme, zdaj_utc())
    return render_template("rezervacije/nova.html", oprema=oprema, obrazec=obrazec,
                           rezultat=rezultat, zasedeni=zasedeni)
