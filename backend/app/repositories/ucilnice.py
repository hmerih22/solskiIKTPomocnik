"""SQL-poizvedbe za tabelo ucilnica."""


def vse(k):
    k.execute("SELECT id, oznaka, naziv, opis FROM ucilnica ORDER BY oznaka")
    return k.fetchall()


def najdi(k, id_ucilnice):
    k.execute("SELECT id, oznaka, naziv, opis FROM ucilnica WHERE id = %s", (id_ucilnice,))
    return k.fetchone()


def najdi_po_oznaki(k, oznaka):
    k.execute("SELECT id FROM ucilnica WHERE oznaka = %s", (oznaka,))
    return k.fetchone()


def ustvari(k, oznaka, naziv, opis):
    k.execute("INSERT INTO ucilnica (oznaka, naziv, opis) VALUES (%s, %s, %s)",
              (oznaka, naziv, opis))
    return k.lastrowid


def posodobi(k, id_ucilnice, naziv, opis):
    k.execute("UPDATE ucilnica SET naziv = %s, opis = %s WHERE id = %s",
              (naziv, opis, id_ucilnice))
