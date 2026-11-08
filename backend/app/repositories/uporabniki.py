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
