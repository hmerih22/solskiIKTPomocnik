"""Pregled opreme (US-01)."""

from flask import Blueprint, render_template
from flask_login import login_required

from .db import transakcija
from .repositories import oprema as repo_oprema

bp = Blueprint("oprema", __name__, url_prefix="/oprema")


@bp.get("/")
@login_required
def seznam():
    """Vsa oprema, tudi nedelujoča (ta ostane vidna z oznako)."""
    with transakcija() as k:
        oprema = repo_oprema.vsa(k)
    return render_template("oprema/seznam.html", oprema=oprema)
