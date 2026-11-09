"""Poslovna pravila rezervacij (US-02, US-03).

Časi so v Pythonu in v bazi vedno v UTC (glej app/cas.py).
"""

from ..cas import zdaj_utc
from ..napake import PoslovnaNapaka


def preveri_termin(zacetek, konec, zdaj=None):
    """Začetek mora biti v prihodnosti in pred koncem (vsi časi v UTC)."""
    if zacetek is None or konec is None:
        raise PoslovnaNapaka("Vnesi začetek in konec rezervacije.")
    if zacetek >= konec:
        raise PoslovnaNapaka("Začetek mora biti pred koncem rezervacije.")
    if zacetek <= (zdaj or zdaj_utc()):
        raise PoslovnaNapaka("Začetek rezervacije mora biti v prihodnosti.")
