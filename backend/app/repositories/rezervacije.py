"""SQL-poizvedbe za tabelo rezervacija."""

# Rezervacija s podatki o opremi in lastniku.
OSNOVNA_POIZVEDBA = """
    SELECT r.id, r.uporabnik_id, r.oprema_id, r.zacetek, r.konec, r.status,
           r.ustvarjena_ob, r.preklicana_ob, r.razlog_preklica,
           o.naziv AS oprema_naziv, o.inventarna_stevilka, o.stanje AS oprema_stanje,
           u.ime AS uporabnik_ime, u.priimek AS uporabnik_priimek
    FROM rezervacija r
    JOIN oprema o ON o.id = r.oprema_id
    JOIN uporabnik u ON u.id = r.uporabnik_id
"""


def prekrivajoce(k, id_opreme, zacetek, konec, zakleni=True):
    """Aktivne rezervacije opreme, ki se prekrivajo s terminom [zacetek, konec).

    Prekrivanje: obstojeca.zacetek < nova.konec IN obstojeca.konec > nova.zacetek.
    Zato se 9.00–10.00 in 10.00–11.00 ne prekrivata, 9.00–10.00 in 9.30–10.30 pa
    se. Preklicane rezervacije ne zasedajo termina.

    Pri shranjevanju (zakleni=True) FOR UPDATE poskrbi, da beremo zadnje
    potrjeno stanje. Pri informativnem preverjanju zaklepanje ni potrebno.
    """
    sql = (
        "SELECT id, zacetek, konec FROM rezervacija"
        " WHERE oprema_id = %s AND status = 'aktivna'"
        " AND zacetek < %s AND konec > %s"
    )
    if zakleni:
        sql += " FOR UPDATE"
    k.execute(sql, (id_opreme, konec, zacetek))
    return k.fetchall()


def zasedeni_termini(k, id_opreme, od):
    """Aktivne rezervacije opreme, ki se končajo po času 'od' (prikaz zasedenosti)."""
    k.execute(
        OSNOVNA_POIZVEDBA
        + " WHERE r.oprema_id = %s AND r.status = 'aktivna' AND r.konec > %s"
        " ORDER BY r.zacetek",
        (id_opreme, od),
    )
    return k.fetchall()
