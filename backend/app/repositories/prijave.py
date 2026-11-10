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


def vse(k, status=None):
    """Vse prijave, po želji samo v podanem stanju; najnovejše najprej."""
    if status:
        k.execute(OSNOVNA_POIZVEDBA + " WHERE p.status = %s ORDER BY p.ustvarjena_ob DESC, p.id DESC",
                  (status,))
    else:
        k.execute(OSNOVNA_POIZVEDBA + " ORDER BY p.ustvarjena_ob DESC, p.id DESC")
    return k.fetchall()


def prevzemi(k, id_prijave, id_skrbnika, cas):
    """Pogojna posodobitev: uspe samo, če je prijava še 'nova' (ADR-0006).

    Vrne število spremenjenih vrstic. Če dva skrbnika prijavo prevzameta
    hkrati, je pri drugem rezultat 0, ker status ni več 'nova'.
    """
    k.execute(
        "UPDATE prijava_tezave SET status = 'v_obravnavi', skrbnik_id = %s, prevzeta_ob = %s"
        " WHERE id = %s AND status = 'nova'",
        (id_skrbnika, cas, id_prijave),
    )
    return k.rowcount


def zakleni(k, id_prijave):
    """Prebere prijavo in zaklene njen zapis do konca transakcije."""
    k.execute(
        "SELECT id, prijavitelj_id, status, skrbnik_id, prevzeta_ob FROM prijava_tezave"
        " WHERE id = %s FOR UPDATE",
        (id_prijave,),
    )
    return k.fetchone()


def zakljuci(k, id_prijave, resitev, cas):
    k.execute(
        "UPDATE prijava_tezave SET status = 'resena', resitev = %s, resena_ob = %s"
        " WHERE id = %s AND status = 'v_obravnavi'",
        (resitev, cas, id_prijave),
    )
    return k.rowcount


def prerazporedi(k, id_prijave, id_skrbnika):
    """Zamenja odgovornega skrbnika; čas prvega prevzema ostane nespremenjen."""
    k.execute(
        "UPDATE prijava_tezave SET skrbnik_id = %s WHERE id = %s AND status = 'v_obravnavi'",
        (id_skrbnika, id_prijave),
    )
    return k.rowcount
