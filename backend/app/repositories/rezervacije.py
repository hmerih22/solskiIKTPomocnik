"""SQL-poizvedbe za tabelo rezervacija."""

# Rezervacija s podatki o opremi, lastniku in preklicatelju.
OSNOVNA_POIZVEDBA = """
    SELECT r.id, r.uporabnik_id, r.oprema_id, r.zacetek, r.konec, r.status,
           r.ustvarjena_ob, r.preklicana_ob, r.preklical_id, r.razlog_preklica,
           r.prevzeta_ob, r.vrnjena_ob,
           o.naziv AS oprema_naziv, o.inventarna_stevilka, o.stanje AS oprema_stanje,
           u.ime AS uporabnik_ime, u.priimek AS uporabnik_priimek,
           p.ime AS preklical_ime, p.priimek AS preklical_priimek
    FROM rezervacija r
    JOIN oprema o ON o.id = r.oprema_id
    JOIN uporabnik u ON u.id = r.uporabnik_id
    LEFT JOIN uporabnik p ON p.id = r.preklical_id
"""


def najdi(k, id_rezervacije):
    k.execute(OSNOVNA_POIZVEDBA + " WHERE r.id = %s", (id_rezervacije,))
    return k.fetchone()


def zakleni(k, id_rezervacije):
    k.execute(
        "SELECT id, uporabnik_id, oprema_id, zacetek, konec, status, prevzeta_ob, vrnjena_ob"
        " FROM rezervacija WHERE id = %s FOR UPDATE",
        (id_rezervacije,),
    )
    return k.fetchone()


def prekrivajoce(k, id_opreme, zacetek, konec, zakleni=True):
    """Aktivne rezervacije opreme, ki se prekrivajo s terminom [zacetek, konec).

    Prekrivanje: obstojeca.zacetek < nova.konec IN obstojeca.konec > nova.zacetek.
    Zato sta 9.00–10.00 in 10.00–11.00 dovoljena (začetek je vključen, konec ne).
    Pri shranjevanju (zakleni=True) FOR UPDATE poskrbi, da beremo zadnje
    potrjeno stanje, ne starega posnetka. Pri informativnem preverjanju
    zaklepanje ni potrebno.
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
    """Aktivne rezervacije opreme, ki se končajo po času 'od' (za prikaz zasedenosti)."""
    k.execute(
        OSNOVNA_POIZVEDBA
        + " WHERE r.oprema_id = %s AND r.status = 'aktivna' AND r.konec > %s"
        " ORDER BY r.zacetek",
        (id_opreme, od),
    )
    return k.fetchall()


def ustvari(k, id_uporabnika, id_opreme, zacetek, konec):
    k.execute(
        "INSERT INTO rezervacija (uporabnik_id, oprema_id, zacetek, konec)"
        " VALUES (%s, %s, %s, %s)",
        (id_uporabnika, id_opreme, zacetek, konec),
    )
    return k.lastrowid


def za_uporabnika(k, id_uporabnika):
    k.execute(
        OSNOVNA_POIZVEDBA + " WHERE r.uporabnik_id = %s ORDER BY r.zacetek DESC",
        (id_uporabnika,),
    )
    return k.fetchall()


def vse(k, samo_prihodnje_od=None):
    """Vse rezervacije; če je podan čas, samo tiste, ki se končajo po njem."""
    if samo_prihodnje_od is None:
        k.execute(OSNOVNA_POIZVEDBA + " ORDER BY r.zacetek DESC")
    else:
        k.execute(
            OSNOVNA_POIZVEDBA + " WHERE r.konec > %s ORDER BY r.zacetek",
            (samo_prihodnje_od,),
        )
    return k.fetchall()


def preklici(k, id_rezervacije, id_preklicatelja, razlog, cas):
    k.execute(
        "UPDATE rezervacija SET status = 'preklicana', preklicana_ob = %s,"
        " preklical_id = %s, razlog_preklica = %s"
        " WHERE id = %s AND status = 'aktivna'",
        (cas, id_preklicatelja, razlog, id_rezervacije),
    )
    return k.rowcount


# --- Nadgradnja F08: prevzem in vračilo -------------------------------------

def izposojena_pri_drugi(k, id_opreme, id_rezervacije):
    """Ali je oprema trenutno prevzeta (in ne vrnjena) pri drugi rezervaciji."""
    k.execute(
        "SELECT id FROM rezervacija"
        " WHERE oprema_id = %s AND id <> %s"
        " AND prevzeta_ob IS NOT NULL AND vrnjena_ob IS NULL",
        (id_opreme, id_rezervacije),
    )
    return k.fetchone() is not None


def zabelezi_prevzem(k, id_rezervacije, cas):
    k.execute(
        "UPDATE rezervacija SET prevzeta_ob = %s WHERE id = %s AND prevzeta_ob IS NULL",
        (cas, id_rezervacije),
    )
    return k.rowcount


def zabelezi_vracilo(k, id_rezervacije, cas):
    k.execute(
        "UPDATE rezervacija SET vrnjena_ob = %s"
        " WHERE id = %s AND prevzeta_ob IS NOT NULL AND vrnjena_ob IS NULL",
        (cas, id_rezervacije),
    )
    return k.rowcount


def izposojene(k):
    """Rezervacije, pri katerih je oprema prevzeta in še ni vrnjena."""
    k.execute(
        OSNOVNA_POIZVEDBA
        + " WHERE r.prevzeta_ob IS NOT NULL AND r.vrnjena_ob IS NULL ORDER BY r.konec"
    )
    return k.fetchall()
