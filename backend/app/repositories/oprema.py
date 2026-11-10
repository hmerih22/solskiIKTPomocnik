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


def najdi_po_inventarni(k, inventarna_stevilka):
    k.execute("SELECT id FROM oprema WHERE inventarna_stevilka = %s", (inventarna_stevilka,))
    return k.fetchone()


def zakleni(k, id_opreme):
    """Prebere opremo in zaklene njen zapis do konca transakcije.

    Vsi postopki, ki ustvarjajo rezervacije ali spreminjajo opremo, najprej
    pokličejo to funkcijo. Druga transakcija, ki želi isti zapis, mora
    počakati, zato se preverjanje in zapis ne moreta prepletati (ADR-0006).
    """
    k.execute(
        "SELECT id, naziv, inventarna_stevilka, vrsta, stanje FROM oprema"
        " WHERE id = %s FOR UPDATE",
        (id_opreme,),
    )
    return k.fetchone()


def ustvari(k, naziv, inventarna_stevilka, vrsta, opis, stanje, ucilnica_id):
    k.execute(
        "INSERT INTO oprema (naziv, inventarna_stevilka, vrsta, opis, stanje, ucilnica_id)"
        " VALUES (%s, %s, %s, %s, %s, %s)",
        (naziv, inventarna_stevilka, vrsta, opis, stanje, ucilnica_id),
    )
    return k.lastrowid


def posodobi(k, id_opreme, naziv, inventarna_stevilka, vrsta, opis, stanje, ucilnica_id):
    k.execute(
        "UPDATE oprema SET naziv = %s, inventarna_stevilka = %s, vrsta = %s, opis = %s,"
        " stanje = %s, ucilnica_id = %s WHERE id = %s",
        (naziv, inventarna_stevilka, vrsta, opis, stanje, ucilnica_id, id_opreme),
    )


def nastavi_stanje(k, id_opreme, stanje):
    k.execute("UPDATE oprema SET stanje = %s WHERE id = %s", (stanje, id_opreme))
