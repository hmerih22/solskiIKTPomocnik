"""SQL-poizvedbe za tabelo oprema."""

# Oprema skupaj s podatki o lokaciji (učilnici).
OSNOVNA_POIZVEDBA = """
    SELECT o.id, o.naziv, o.inventarna_stevilka, o.vrsta, o.opis, o.stanje,
           o.ucilnica_id, u.oznaka AS ucilnica_oznaka, u.naziv AS ucilnica_naziv
    FROM oprema o
    JOIN ucilnica u ON u.id = o.ucilnica_id
"""


def vsa(k):
    k.execute(OSNOVNA_POIZVEDBA + " ORDER BY o.vrsta, o.naziv")
    return k.fetchall()


def najdi(k, id_opreme):
    k.execute(OSNOVNA_POIZVEDBA + " WHERE o.id = %s", (id_opreme,))
    return k.fetchone()
