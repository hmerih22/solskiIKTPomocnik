"""Prijave težav: oddaja, pregled (US-05), obravnava (US-06),
komentarji (US-09) in priponke (US-10)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from .auth import zahteva_vlogo
from .db import transakcija
from .napake import PoslovnaNapaka
from .obrazci import (
    ObrazecKomentar,
    ObrazecPrazen,
    ObrazecPrerazporeditev,
    ObrazecPrijavaTezave,
    ObrazecResitev,
)
from .repositories import oprema as repo_oprema
from .repositories import prijave as repo_prijave
from .repositories import ucilnice as repo_ucilnice
from .repositories import uporabniki as repo_uporabniki
from .services import prijave as storitev

bp = Blueprint("prijave", __name__, url_prefix="/prijave")

STATUSI = {"nova": "Nova", "v_obravnavi": "V obravnavi", "resena": "Rešena"}


def _najdi_ali_404(k, id_prijave):
    prijava = repo_prijave.najdi(k, id_prijave)
    if prijava is None:
        abort(404)
    if not storitev.lahko_vidi(current_user, prijava):
        # Učitelj ne sme brati tuje prijave (US-05).
        abort(403)
    return prijava


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
        obrazec.ucilnica_id.data = request.args.get("ucilnica_id", 0, type=int)

    if obrazec.validate_on_submit():
        try:
            id_prijave = storitev.oddaj(
                current_user, obrazec.oprema_id.data, obrazec.ucilnica_id.data,
                obrazec.naslov.data, obrazec.opis.data, obrazec.priponke.data,
            )
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
        else:
            flash("Prijava je oddana.", "uspeh")
            return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave))

    return render_template("prijave/nova.html", obrazec=obrazec)


@bp.get("/moje")
@login_required
def moje():
    with transakcija() as k:
        prijave = repo_prijave.za_prijavitelja(k, current_user.id)
    return render_template("prijave/seznam.html", prijave=prijave, naslov="Moje prijave",
                           statusi=STATUSI, filter_status=None, vse=False)


@bp.get("/vse")
@zahteva_vlogo("ikt_skrbnik")
def vse():
    status = request.args.get("status")
    if status not in STATUSI:
        status = None
    with transakcija() as k:
        prijave = repo_prijave.vse(k, status)
    return render_template("prijave/seznam.html", prijave=prijave, naslov="Vse prijave",
                           statusi=STATUSI, filter_status=status, vse=True)


@bp.get("/<int:id_prijave>")
@login_required
def podrobnosti(id_prijave):
    """Zaslon WF-03: podrobnosti in obravnava prijave."""
    with transakcija() as k:
        prijava = _najdi_ali_404(k, id_prijave)
        komentarji = repo_prijave.komentarji(k, id_prijave)
        priponke = repo_prijave.priponke(k, id_prijave)
        skrbniki = repo_uporabniki.aktivni_skrbniki(k) if current_user.je_administrator else []

    prerazporeditev = ObrazecPrerazporeditev()
    prerazporeditev.skrbnik_id.choices = [
        (s["id"], f"{s['ime']} {s['priimek']}") for s in skrbniki
    ]
    prerazporeditev.skrbnik_id.data = prijava["skrbnik_id"]

    return render_template(
        "prijave/podrobnosti.html",
        prijava=prijava, komentarji=komentarji, priponke=priponke, statusi=STATUSI,
        prazen=ObrazecPrazen(), resitev=ObrazecResitev(), komentar=ObrazecKomentar(),
        prerazporeditev=prerazporeditev,
        lahko_zakljuci=storitev.lahko_zakljuci(current_user, prijava),
        lahko_komentira=storitev.lahko_komentira(current_user, prijava),
    )


@bp.post("/<int:id_prijave>/prevzem")
@zahteva_vlogo("ikt_skrbnik")
def prevzem(id_prijave):
    if not ObrazecPrazen().validate_on_submit():
        abort(400)
    try:
        storitev.prevzemi(current_user, id_prijave)
        flash("Prijavo si prevzel. Zdaj si zanjo odgovoren.", "uspeh")
    except PoslovnaNapaka as e:
        flash(e.sporocilo, "napaka")
    return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave))


@bp.post("/<int:id_prijave>/zakljucek")
@zahteva_vlogo("ikt_skrbnik")
def zakljucek(id_prijave):
    obrazec = ObrazecResitev()
    if not obrazec.validate_on_submit():
        for napake in obrazec.errors.values():
            for napaka in napake:
                flash(napaka, "napaka")
    else:
        try:
            storitev.zakljuci(current_user, id_prijave, obrazec.resitev.data)
            flash("Prijava je zaključena kot rešena.", "uspeh")
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave))


@bp.post("/<int:id_prijave>/prerazporeditev")
@zahteva_vlogo("administrator")
def prerazporeditev(id_prijave):
    # Seznam možnih skrbnikov preveri storitev (aktiven, ustrezna vloga),
    # zato tu preverimo le CSRF in preberemo izbrani id.
    if not ObrazecPrazen().validate_on_submit():
        abort(400)
    id_skrbnika = request.form.get("skrbnik_id", type=int)
    try:
        storitev.prerazporedi(current_user, id_prijave, id_skrbnika)
        flash("Prijava je prerazporejena.", "uspeh")
    except PoslovnaNapaka as e:
        flash(e.sporocilo, "napaka")
    return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave))


@bp.post("/<int:id_prijave>/komentar")
@login_required
def komentar(id_prijave):
    obrazec = ObrazecKomentar()
    if not obrazec.validate_on_submit():
        flash("Komentar ne sme biti prazen.", "napaka")
    else:
        try:
            storitev.dodaj_komentar(current_user, id_prijave, obrazec.besedilo.data)
            flash("Komentar je dodan.", "uspeh")
        except PoslovnaNapaka as e:
            flash(e.sporocilo, "napaka")
    return redirect(url_for("prijave.podrobnosti", id_prijave=id_prijave) + "#komentarji")


@bp.get("/priponka/<int:id_priponke>")
@login_required
def priponka(id_priponke):
    """Prenos priponke – samo za uporabnike, ki smejo videti prijavo (US-10)."""
    with transakcija() as k:
        priponka = repo_prijave.najdi_priponko(k, id_priponke)
        if priponka is None:
            abort(404)
        _najdi_ali_404(k, priponka["prijava_id"])

    pot = storitev.mapa_priponk() / priponka["shranjeno_ime"]
    if not pot.is_file():
        abort(404)
    odgovor = send_file(pot, mimetype=priponka["vrsta"], download_name=priponka["izvirno_ime"],
                        as_attachment=priponka["vrsta"] == "application/pdf")
    # Brskalnik ne sme ugibati vrste datoteke (npr. je obravnavati kot HTML).
    odgovor.headers["X-Content-Type-Options"] = "nosniff"
    return odgovor
