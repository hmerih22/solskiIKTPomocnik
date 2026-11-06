"""Storitve: poslovna pravila in transakcijski postopki.

Storitev prejme podatke iz poti (views), preveri pravice in pravila, v
transakciji pokliče repozitorije in vrne rezultat. Ob kršitvi pravila
sproži PoslovnaNapaka, ob kršitvi pravic pa Prepovedano (glej napake.py).
Storitve ne vedo nič o HTML ali obrazcih, zato jih je lahko testirati.
"""
