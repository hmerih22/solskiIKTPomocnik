"""SQL-poizvedbe za tabelo obvestilo (nadgradnja F11)."""


def zabelezi(k, prejemnik, zadeva, besedilo, status, napaka=None):
    k.execute(
        "INSERT INTO obvestilo (prejemnik, zadeva, besedilo, status, napaka)"
        " VALUES (%s, %s, %s, %s, %s)",
        (prejemnik, zadeva, besedilo, status, napaka),
    )
    return k.lastrowid


def zadnja(k, omejitev=100):
    k.execute(
        "SELECT id, prejemnik, zadeva, besedilo, ustvarjeno_ob, status, napaka"
        " FROM obvestilo ORDER BY ustvarjeno_ob DESC, id DESC LIMIT %s",
        (omejitev,),
    )
    return k.fetchall()
