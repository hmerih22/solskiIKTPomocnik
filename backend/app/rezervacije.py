"""Rezervacije: preverjanje termina, rezervacija, pregled, preklic (US-02–US-04)
ter prevzem in vračilo opreme (nadgradnja US-08)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .auth import zahteva_vlogo
from .cas import v_utc, zdaj_utc
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import ObrazecPrazen, ObrazecPreklic, ObrazecTermin
from .pomocniki import pot_nazaj
from .repositories import oprema as repo_oprema
from .repositories import rezervacije as repo_rezervacije
from .services import rezervacije as storitev

bp = Blueprint("rezervacije", __name__, url_prefix="/rezervacije")


@bp.route("/nova/<int:id_opreme>", methods=["GET", "POST"])
@login_required
def nova(id_opreme):
    """Zaslon WF-02: izbira termina, »Preveri termin« in »Potrdi rezervacijo«."""
    obrazec = ObrazecTermin()
    rezultat = None

    if obrazec.validate_on_submit():
        zacetek = v_utc(obrazec.zacetek.data)
        konec = v_utc(obrazec.konec.data)
        try:
            if obrazec.potrdi.data:
                storitev.ustvari(current_user, id_opreme, zacetek, konec)
                flash("Rezervacija je potrjena.", "uspeh")
                return redirect(url_for("rezervacije.moje"))
            rezultat = storitev.preveri_razpolozljivost(id_opreme, zacetek, konec)
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")

    with transakcija() as k:
        oprema = repo_oprema.najdi(k, id_opreme)
        if oprema is None:
            abort(404)
        zasedeni = repo_rezervacije.zasedeni_termini(k, id_opreme, zdaj_utc())

    return render_template("rezervacije/nova.html", oprema=oprema, obrazec=obrazec,
                           rezultat=rezultat, zasedeni=zasedeni)


@bp.get("/moje")
@login_required
def moje():
    with transakcija() as k:
        rezervacije = repo_rezervacije.za_uporabnika(k, current_user.id)
    return render_template("rezervacije/moje.html", rezervacije=rezervacije,
                           obrazec=ObrazecPreklic(), zdaj=zdaj_utc(),
                           lahko_preklice=storitev.lahko_preklice)


@bp.get("/vse")
@zahteva_vlogo("ikt_skrbnik")
def vse():
    """Zaslon WF-04: vse rezervacije (privzeto samo prihodnje in tekoče)."""
    prikazi_vse = request.args.get("prikaz") == "vse"
    with transakcija() as k:
        rezervacije = repo_rezervacije.vse(k, None if prikazi_vse else zdaj_utc())
    return render_template("rezervacije/vse.html", rezervacije=rezervacije,
                           obrazec=ObrazecPreklic(), prazen=ObrazecPrazen(),
                           zdaj=zdaj_utc(), prikazi_vse=prikazi_vse,
                           lahko_preklice=storitev.lahko_preklice)


@bp.post("/<int:id_rezervacije>/preklic")
@login_required
def preklic(id_rezervacije):
    obrazec = ObrazecPreklic()
    if not obrazec.validate_on_submit():
        flash("Obrazec ni veljaven. Poskusi znova.", "napaka")
    else:
        try:
            storitev.preklici(current_user, id_rezervacije, obrazec.razlog.data)
            flash("Rezervacija je preklicana.", "uspeh")
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return redirect(pot_nazaj("rezervacije.moje"))


# --- Nadgradnja F08: prevzem in vračilo -------------------------------------

@bp.get("/izposoja")
@zahteva_vlogo("ikt_skrbnik")
def izposoja():
    with transakcija() as k:
        izposojene = repo_rezervacije.izposojene(k)
    return render_template("rezervacije/izposoja.html", izposojene=izposojene,
                           prazen=ObrazecPrazen(), zdaj=zdaj_utc())


@bp.post("/<int:id_rezervacije>/prevzem")
@zahteva_vlogo("ikt_skrbnik")
def prevzem(id_rezervacije):
    return _izvedi(storitev.zabelezi_prevzem, id_rezervacije, "Prevzem opreme je zabeležen.")


@bp.post("/<int:id_rezervacije>/vracilo")
@zahteva_vlogo("ikt_skrbnik")
def vracilo(id_rezervacije):
    return _izvedi(storitev.zabelezi_vracilo, id_rezervacije, "Vračilo opreme je zabeleženo.")


def _izvedi(operacija, id_rezervacije, sporocilo):
    if not ObrazecPrazen().validate_on_submit():
        abort(400)
    try:
        operacija(current_user, id_rezervacije)
        flash(sporocilo, "uspeh")
    except PoslovnaNapaka as e:
        flash(e.sporocilo, "napaka")
    return redirect(pot_nazaj("rezervacije.vse"))

