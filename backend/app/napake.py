"""Napake poslovne logike.

Storitve (services/) ob kršitvi pravila sprožijo PoslovnaNapaka s sporočilom,
ki ga lahko pokažemo uporabniku. Poti (views) jo ujamejo in sporočilo
prikažejo s flash(). Ker se napaka sproži znotraj transakcija(), se vse
spremembe te zahteve razveljavijo.

Kršitev pravic (npr. učitelj poskuša prevzeti prijavo) ni PoslovnaNapaka,
ampak Prepovedano, ki ga aplikacija pretvori v odgovor 403.
"""


class PoslovnaNapaka(Exception):
    """Operacije ni mogoče izvesti zaradi poslovnega pravila."""

    def __init__(self, sporocilo):
        super().__init__(sporocilo)
        self.sporocilo = sporocilo


class Prepovedano(Exception):
    """Uporabnik nima pravice za to operacijo (odgovor 403).

    Storitev to preveri sama, zato pravila veljajo tudi, če bi kdo zahtevo
    poslal neposredno, mimo uporabniškega vmesnika.
    """
