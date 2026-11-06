"""SQL-poizvedbe za statistiko (nadgradnja F12).

Vse funkcije prejmejo interval [od, do) v UTC.
"""


def rezervacije_po_opremi(k, od, do):
    """Nepreklicane rezervacije, katerih začetek je v obdobju, po opremi."""
    k.execute(
        "SELECT o.id, o.naziv, o.inventarna_stevilka, COUNT(r.id) AS stevilo"
        " FROM oprema o"
        " LEFT JOIN rezervacija r ON r.oprema_id = o.id"
        "   AND r.status = 'aktivna' AND r.zacetek >= %s AND r.zacetek < %s"
        " GROUP BY o.id, o.naziv, o.inventarna_stevilka"
        " ORDER BY stevilo DESC, o.naziv",
        (od, do),
    )
    return k.fetchall()


def prijave_po_opremi(k, od, do):
    k.execute(
        "SELECT o.id, o.naziv, o.inventarna_stevilka, COUNT(p.id) AS stevilo"
        " FROM oprema o"
        " JOIN prijava_tezave p ON p.oprema_id = o.id"
        "   AND p.ustvarjena_ob >= %s AND p.ustvarjena_ob < %s"
        " GROUP BY o.id, o.naziv, o.inventarna_stevilka"
        " ORDER BY stevilo DESC, o.naziv",
        (od, do),
    )
    return k.fetchall()


def prijave_po_ucilnicah(k, od, do):
    k.execute(
        "SELECT u.id, u.oznaka, u.naziv, COUNT(p.id) AS stevilo"
        " FROM ucilnica u"
        " JOIN prijava_tezave p ON p.ucilnica_id = u.id"
        "   AND p.ustvarjena_ob >= %s AND p.ustvarjena_ob < %s"
        " GROUP BY u.id, u.oznaka, u.naziv"
        " ORDER BY stevilo DESC, u.oznaka",
        (od, do),
    )
    return k.fetchall()


def stevilo_prijav(k, od, do):
    """Skupno število prijav; prijava z opremo in učilnico se šteje enkrat."""
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM prijava_tezave"
        " WHERE ustvarjena_ob >= %s AND ustvarjena_ob < %s",
        (od, do),
    )
    return k.fetchone()["stevilo"]


def stevilo_rezervacij(k, od, do):
    k.execute(
        "SELECT COUNT(*) AS stevilo FROM rezervacija"
        " WHERE status = 'aktivna' AND zacetek >= %s AND zacetek < %s",
        (od, do),
    )
    return k.fetchone()["stevilo"]


def povprecni_cas_resevanja(k, od, do):
    """Povprečje sekund od oddaje do zaključka za prijave, zaključene v obdobju.

    Vrne None, če v obdobju ni zaključenih prijav.
    """
    k.execute(
        "SELECT AVG(TIMESTAMPDIFF(SECOND, ustvarjena_ob, resena_ob)) AS sekunde,"
        " COUNT(*) AS stevilo"
        " FROM prijava_tezave"
        " WHERE status = 'resena' AND resena_ob >= %s AND resena_ob < %s",
        (od, do),
    )
    vrstica = k.fetchone()
    if not vrstica["stevilo"]:
        return None
    return float(vrstica["sekunde"])
