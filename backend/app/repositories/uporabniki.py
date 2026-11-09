"""SQL-poizvedbe za tabelo uporabnik."""

STOLPCI = "id, ime, priimek, email, geslo_hash, vloga, aktiven, ustvarjen_ob"


def najdi(k, id_uporabnika):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE id = %s", (id_uporabnika,))
    return k.fetchone()


def najdi_po_emailu(k, email):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE email = %s", (email,))
    return k.fetchone()


def ustvari(k, ime, priimek, email, geslo_hash, vloga):
    k.execute(
        "INSERT INTO uporabnik (ime, priimek, email, geslo_hash, vloga)"
        " VALUES (%s, %s, %s, %s, %s)",
        (ime, priimek, email, geslo_hash, vloga),
    )
    return k.lastrowid


def vsi(k):
    k.execute(f"SELECT {STOLPCI} FROM uporabnik ORDER BY priimek, ime")
    return k.fetchall()


def zakleni(k, id_uporabnika):
    """Prebere uporabnika in zaklene njegov zapis do konca transakcije."""
    k.execute(f"SELECT {STOLPCI} FROM uporabnik WHERE id = %s FOR UPDATE", (id_uporabnika,))
    return k.fetchone()


def posodobi(k, id_uporabnika, ime, priimek, email, vloga, aktiven):
    k.execute(
        "UPDATE uporabnik SET ime = %s, priimek = %s, email = %s, vloga = %s, aktiven = %s"
        " WHERE id = %s",
        (ime, priimek, email, vloga, aktiven, id_uporabnika),
    )


def stevilo_odprtih_prijav(k, id_uporabnika):
    """Število prijav v obravnavi, ki jih je uporabnik prevzel in še niso rešene."""
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM prijava_tezave"
        " WHERE skrbnik_id = %s AND status = 'v_obravnavi'",
        (id_uporabnika,),
    )
    return k.fetchone()["stevilo"]


def stevilo_aktivnih_administratorjev(k):
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM uporabnik"
        " WHERE vloga = 'administrator' AND aktiven = TRUE"
    )
    return k.fetchone()["stevilo"]
