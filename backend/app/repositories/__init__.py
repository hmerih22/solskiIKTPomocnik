"""Repozitoriji: vse SQL-poizvedbe aplikacije, ena datoteka na tabelo.

Vsaka funkcija prejme kazalec (cursor) kot prvi argument. Tako lahko
storitev več poizvedb izvede v isti transakciji:

    with transakcija() as k:
        oprema = repo_oprema.zakleni(k, id_opreme)
        ...

Vrednosti se vedno podajo kot parametri (%s), nikoli z lepljenjem besedila
v SQL – tako je aplikacija zaščitena pred SQL injection.
Kazalec je ustvarjen z dictionary=True, zato so vrstice slovarji.
"""
