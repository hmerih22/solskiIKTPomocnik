"""Vloge uporabnikov, od najmanj do največ pravic.

Višja vloga ima vse pravice nižjih (administrator je tudi IKT skrbnik).
"""

VLOGE = ["ucitelj", "ikt_skrbnik", "administrator"]
NAZIVI_VLOG = {
    "ucitelj": "Učitelj",
    "ikt_skrbnik": "IKT skrbnik",
    "administrator": "Administrator",
}
