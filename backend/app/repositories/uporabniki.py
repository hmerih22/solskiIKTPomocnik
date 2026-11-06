"""SQL-poizvedbe za tabelo uporabnik."""

STOLPCI = "id, ime, priimek, email, geslo_hash, vloga, aktiven, ustvarjen_ob"


def najdi(k, id_uporabnika):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE id = %s", (id_uporabnika,))
    return k.fetchone()


def zakleni(k, id_uporabnika):
    """Prebere uporabnika in zaklene njegov zapis do konca transakcije."""
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE id = %s FOR UPDATE", (id_uporabnika,))
    return k.fetchone()


def najdi_po_emailu(k, email):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE email = %s", (email,))
    return k.fetchone()


def vsi(k):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik ORDER BY priimek, ime")
    return k.fetchall()


def aktivni_skrbniki(k):
    """Uporabniki, ki lahko obravnavajo prijave (IKT skrbnik ali administrator)."""
    k.execute(
        f"SELECT {STOLPCI} FROM uporabnik"
        " WHERE aktiven = TRUE AND vloga IN ('ikt_skrbnik', 'administrator')"
        " ORDER BY priimek, ime"
    )
    return k.fetchall()


def ustvari(k, ime, priimek, email, geslo_hash, vloga):
    k.execute(
        "INSERT INTO uporabnik (ime, priimek, email, geslo_hash, vloga)"
        " VALUES (%s, %s, %s, %s, %s)",
        (ime, priimek, email, geslo_hash, vloga),
    )
    return k.lastrowid


def posodobi(k, id_uporabnika, ime, priimek, email, vloga, aktiven):
    k.execute(
        "UPDATE uporabnik SET ime = %s, priimek = %s, email = %s, vloga = %s, aktiven = %s"
        " WHERE id = %s",
        (ime, priimek, email, vloga, aktiven, id_uporabnika),
    )


def nastavi_geslo(k, id_uporabnika, geslo_hash):
    k.execute("UPDATE uporabnik SET geslo_hash = %s WHERE id = %s", (geslo_hash, id_uporabnika))


def stevilo_odprtih_prijav(k, id_uporabnika):
    """Število prijav v obravnavi, za katere je uporabnik odgovoren."""
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM prijava_tezave"
        " WHERE skrbnik_id = %s AND status = 'v_obravnavi'",
        (id_uporabnika,),
    )
    return k.fetchone()["stevilo"]


def stevilo_administratorjev(k):
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM uporabnik"
        " WHERE vloga = 'administrator' AND aktiven = TRUE"
    )
    return k.fetchone()["stevilo"]
