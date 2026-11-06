"""Statistika uporabe opreme in težav (nadgradnja F12, US-12)."""

from datetime import datetime, time, timedelta

from flask import Blueprint, flash, render_template, request

from .auth import zahteva_vlogo
from .cas import v_lokalni, v_utc, zdaj_utc
from .db import transakcija
from .obrazci import ObrazecObdobje
from .repositories import statistika as repo

bp = Blueprint("statistika", __name__, url_prefix="/statistika")


def obdobje_v_utc(od, do):
    """Vključujoča lokalna datuma [od, do] pretvori v UTC interval [začetek, konec).

    Primer: 1. 11.–30. 11. pomeni od 1. 11. 00:00 do 1. 12. 00:00 lokalnega časa.
    """
    zacetek = v_utc(datetime.combine(od, time.min))
    konec = v_utc(datetime.combine(do + timedelta(days=1), time.min))
    return zacetek, konec


def oblikuj_trajanje(sekunde):
    if sekunde is None:
        return "Ni podatkov"
    minute = round(sekunde / 60)
    dni, minute = divmod(minute, 24 * 60)
    ure, minute = divmod(minute, 60)
    deli = []
    if dni:
        deli.append(f"{dni} d")
    if ure or dni:
        deli.append(f"{ure} h")
    deli.append(f"{minute} min")
    return " ".join(deli)


@bp.get("/")
@zahteva_vlogo("ikt_skrbnik")
def pregled():
    # Obrazec je poslan z GET, zato podatke beremo iz request.args.
    obrazec = ObrazecObdobje(request.args)
    danes = v_lokalni(zdaj_utc()).date()
    if not obrazec.od.raw_data:
        # Privzeto: zadnjih 30 dni.
        obrazec.od.data = danes - timedelta(days=29)
        obrazec.do.data = danes

    podatki = None
    if obrazec.od.raw_data and not obrazec.validate():
        pass  # napake obrazca se prikažejo v predlogi
    elif obrazec.od.data > obrazec.do.data:
        flash("Začetni datum mora biti pred končnim ali enak njemu.", "napaka")
    else:
        od, do = obdobje_v_utc(obrazec.od.data, obrazec.do.data)
        with transakcija() as k:
            podatki = {
                "stevilo_rezervacij": repo.stevilo_rezervacij(k, od, do),
                "stevilo_prijav": repo.stevilo_prijav(k, od, do),
                "rezervacije_po_opremi": repo.rezervacije_po_opremi(k, od, do),
                "prijave_po_opremi": repo.prijave_po_opremi(k, od, do),
                "prijave_po_ucilnicah": repo.prijave_po_ucilnicah(k, od, do),
                "povprecni_cas": oblikuj_trajanje(repo.povprecni_cas_resevanja(k, od, do)),
            }
    return render_template("statistika/pregled.html", obrazec=obrazec, podatki=podatki)
