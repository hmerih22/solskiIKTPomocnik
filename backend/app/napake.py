"""Napake poslovne logike.

Storitve (services/) ob kršitvi pravila sprožijo PoslovnaNapaka s sporočilom,
ki ga lahko pokažemo uporabniku. Poti jo ujamejo in sporočilo prikažejo s
flash(). Ker se napaka sproži znotraj transakcija(), se vse spremembe te
zahteve razveljavijo.
"""


class PoslovnaNapaka(Exception):
    """Operacije ni mogoče izvesti zaradi poslovnega pravila."""

    def __init__(self, sporocilo):
        super().__init__(sporocilo)
        self.sporocilo = sporocilo
