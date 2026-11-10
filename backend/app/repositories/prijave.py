"""SQL-poizvedbe za tabelo prijava_tezave."""

# Prijava s podatki o prijavitelju, skrbniku, opremi in učilnici.
OSNOVNA_POIZVEDBA = """
    SELECT p.id, p.prijavitelj_id, p.oprema_id, p.ucilnica_id, p.naslov, p.opis,
           p.status, p.skrbnik_id, p.ustvarjena_ob, p.prevzeta_ob, p.resitev, p.resena_ob,
           pr.ime AS prijavitelj_ime, pr.priimek AS prijavitelj_priimek,
           s.ime AS skrbnik_ime, s.priimek AS skrbnik_priimek,
           o.naziv AS oprema_naziv, o.inventarna_stevilka, o.stanje AS oprema_stanje,
           u.oznaka AS ucilnica_oznaka, u.naziv AS ucilnica_naziv
    FROM prijava_tezave p
    JOIN uporabnik pr ON pr.id = p.prijavitelj_id
    LEFT JOIN uporabnik s ON s.id = p.skrbnik_id
    LEFT JOIN oprema o ON o.id = p.oprema_id
    LEFT JOIN ucilnica u ON u.id = p.ucilnica_id
"""


def najdi(k, id_prijave):
    k.execute(OSNOVNA_POIZVEDBA + " WHERE p.id = %s", (id_prijave,))
    return k.fetchone()


def ustvari(k, id_prijavitelja, id_opreme, id_ucilnice, naslov, opis):
    """Nova prijava ima privzeto status 'nova' in nima skrbnika."""
    k.execute(
        "INSERT INTO prijava_tezave (prijavitelj_id, oprema_id, ucilnica_id, naslov, opis)"
        " VALUES (%s, %s, %s, %s, %s)",
        (id_prijavitelja, id_opreme, id_ucilnice, naslov, opis),
    )
    return k.lastrowid


def za_prijavitelja(k, id_uporabnika):
    k.execute(
        OSNOVNA_POIZVEDBA + " WHERE p.prijavitelj_id = %s ORDER BY p.ustvarjena_ob DESC, p.id DESC",
        (id_uporabnika,),
    )
    return k.fetchall()
