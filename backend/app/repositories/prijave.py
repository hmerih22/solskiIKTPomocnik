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


def zakleni(k, id_prijave):
    k.execute(
        "SELECT id, prijavitelj_id, status, skrbnik_id FROM prijava_tezave"
        " WHERE id = %s FOR UPDATE",
        (id_prijave,),
    )
    return k.fetchone()


def za_prijavitelja(k, id_uporabnika):
    k.execute(
        OSNOVNA_POIZVEDBA + " WHERE p.prijavitelj_id = %s ORDER BY p.ustvarjena_ob DESC",
        (id_uporabnika,),
    )
    return k.fetchall()


def vse(k, status=None):
    if status:
        k.execute(
            OSNOVNA_POIZVEDBA + " WHERE p.status = %s ORDER BY p.ustvarjena_ob DESC",
            (status,),
        )
    else:
        k.execute(OSNOVNA_POIZVEDBA + " ORDER BY p.ustvarjena_ob DESC")
    return k.fetchall()


def ustvari(k, id_prijavitelja, id_opreme, id_ucilnice, naslov, opis):
    k.execute(
        "INSERT INTO prijava_tezave (prijavitelj_id, oprema_id, ucilnica_id, naslov, opis)"
        " VALUES (%s, %s, %s, %s, %s)",
        (id_prijavitelja, id_opreme, id_ucilnice, naslov, opis),
    )
    return k.lastrowid


def prevzemi(k, id_prijave, id_skrbnika, cas):
    """Pogojna posodobitev: uspe samo, če je prijava še 'nova' (ADR-0006).

    Vrne število spremenjenih vrstic. Če sta dva skrbnika prijavo prevzela
    hkrati, bo pri drugem vrnjena 0, ker status ni več 'nova'.
    """
    k.execute(
        "UPDATE prijava_tezave SET status = 'v_obravnavi', skrbnik_id = %s, prevzeta_ob = %s"
        " WHERE id = %s AND status = 'nova'",
        (id_skrbnika, cas, id_prijave),
    )
    return k.rowcount


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


# --- Nadgradnja F09: komentarji ---------------------------------------------

def komentarji(k, id_prijave):
    k.execute(
        "SELECT c.id, c.besedilo, c.ustvarjen_ob, u.ime, u.priimek"
        " FROM komentar_prijave c JOIN uporabnik u ON u.id = c.avtor_id"
        " WHERE c.prijava_id = %s ORDER BY c.ustvarjen_ob, c.id",
        (id_prijave,),
    )
    return k.fetchall()


def dodaj_komentar(k, id_prijave, id_avtorja, besedilo):
    k.execute(
        "INSERT INTO komentar_prijave (prijava_id, avtor_id, besedilo) VALUES (%s, %s, %s)",
        (id_prijave, id_avtorja, besedilo),
    )
    return k.lastrowid


# --- Nadgradnja F10: priponke -----------------------------------------------

def priponke(k, id_prijave):
    k.execute(
        "SELECT id, prijava_id, izvirno_ime, shranjeno_ime, vrsta, velikost"
        " FROM priponka_prijave WHERE prijava_id = %s ORDER BY id",
        (id_prijave,),
    )
    return k.fetchall()


def najdi_priponko(k, id_priponke):
    k.execute(
        "SELECT id, prijava_id, izvirno_ime, shranjeno_ime, vrsta, velikost"
        " FROM priponka_prijave WHERE id = %s",
        (id_priponke,),
    )
    return k.fetchone()


def dodaj_priponko(k, id_prijave, izvirno_ime, shranjeno_ime, vrsta, velikost):
    k.execute(
        "INSERT INTO priponka_prijave (prijava_id, izvirno_ime, shranjeno_ime, vrsta, velikost)"
        " VALUES (%s, %s, %s, %s, %s)",
        (id_prijave, izvirno_ime, shranjeno_ime, vrsta, velikost),
    )
    return k.lastrowid
