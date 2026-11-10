# Šolski IKT pomočnik

Spletna aplikacija za **rezervacijo skupne šolske IKT-opreme** (prenosniki, projektorji, kompleti tablic) ter **prijavo in obravnavo tehničnih težav** znotraj ene šole.

Narejen je celoten obseg MVP: prijava in vloge (učitelj, IKT skrbnik, administrator), upravljanje uporabnikov, učilnic in opreme, preverjanje razpoložljivosti, rezervacija brez prekrivanja terminov, pregled in preklic rezervacij, prijava težav, njihova obravnava (prevzem, zaključek, prerazporeditev) ter označevanje nedelujoče opreme.

Uporabljene tehnologije: Python 3 s Flaskom, MySQL 8.4, Jinja predloge, Flask-Login in Flask-WTF.

## Namestitev in zagon (Windows PowerShell)

Vsi ukazi se izvedejo v korenski mapi projekta.

### 1. Virtualno okolje in knjižnice

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Nastavitve (.env)

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

V datoteko `.env` vpiši izpisano vrednost kot `SECRET_KEY` in izberi geslo za bazo (`DB_PASSWORD`). Datoteka `.env` se ne shrani v Git. Če katera obvezna nastavitev manjka, aplikacija ob zagonu izpiše, katera.

### 3. Baza

Kopiraj pripravljalno skripto in vanjo namesto `GESLO_APLIKACIJE` vpiši isto geslo kot `DB_PASSWORD` v `.env`:

```powershell
Copy-Item backend\sql\000-priprava.example.sql backend\sql\local-priprava.sql
```

Nato skripto izvedi kot uporabnik `root`:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 -e "source backend/sql/local-priprava.sql"
```

Skripta izbriše in na novo ustvari bazi `solski_ikt` (glavna) in `solski_ikt_test` (za teste), ustvari uporabnika `solski_ikt_app` in naloži shemo iz `backend/sql/001-schema.sql`. Datoteke `local-*.sql` so v `.gitignore`, ker vsebujejo geslo.

### 4. Prvi administrator

```powershell
flask --app backend/app create-admin
```

Ukaz vpraša za ime, priimek, e-poštni naslov in geslo (vsaj 8 znakov). Javne registracije ni: nadaljnje račune ustvari administrator v aplikaciji (meni **Uporabniki**).

### 5. Zagon

```powershell
flask --app backend/app run --debug
```

Aplikacija je dostopna na <http://127.0.0.1:5000>.

## Testi

```powershell
python -m pytest
```

Testi z bazo uporabljajo ločeno bazo `solski_ikt_test` in jo pred vsakim testom izpraznijo, glavne baze ne spreminjajo. Če baza ni dosegljiva, se ti testi preskočijo (razlog izpiše `python -m pytest -rs`).

## Zgradba kode

| Pot | Vsebina |
| --- | --- |
| `backend/app/__init__.py` | `create_app`: nastavitve, registracija modulov, strani z napakami |
| `backend/app/config.py` | Branje nastavitev iz `.env` |
| `backend/app/db.py` | Povezava z bazo na zahtevo, pomočnik `transakcija()` |
| `backend/app/auth.py` | Prijava, odjava, nalaganje uporabnika, dekorator `zahteva_vlogo` |
| `backend/app/vloge.py` | Seznam vlog in njihovi nazivi |
| `backend/app/admin.py` | Strani za administratorja (uporabniki) |
| `backend/app/services/` | Poslovna pravila (npr. preverjanje podatkov novega računa) |
| `backend/app/repositories/` | SQL-poizvedbe s parametri `%s` |
| `backend/app/obrazci.py` | Obrazci Flask-WTF z zaščito CSRF |
| `backend/app/cli.py` | Ukaz `create-admin` |
| `backend/sql/` | Shema baze in pripravljalna skripta |
| `backend/tests/` | Testi (pytest) |
| `frontend/templates/`, `frontend/static/` | Jinja predloge in CSS |
| `docs/` | Projektna dokumentacija |

## Dokumentacija

| Dokument | Vsebina |
| --- | --- |
| [01 – Zasnova rešitve](docs/01-zasnova-resitve.md) | Ideja, problem, ciljni uporabniki in primer uporabe |
| [02 – Funkcionalnosti in obseg](docs/02-funkcionalnosti-in-obseg.md) | Vloge, funkcionalnosti, obseg MVP in nadgradnje |
| [03 – Podatkovni model](docs/03-podatkovni-model.md) | Entitete, povezave, omejitve in indeksi |
| [04 – Arhitektura in tehnološki sklad](docs/04-arhitektura-in-tehnoloski-sklad.md) | Zgradba sistema, tehnologije in lokalni zagon |
| [05 – Uporabniške zgodbe](docs/05-uporabniske-zgodbe.md) | Uporabniške zgodbe s sprejemnimi kriteriji |
| [06 – Wireframes](docs/06-wireframes.md) | Žični prikazi ključnih zaslonov |
| [Arhitekturne odločitve (ADR)](docs/adr/) | Zapisi arhitekturnih odločitev po predlogi MADR |

## Način dela (GitHub Flow)

Vse spremembe nastanejo na ločeni veji (npr. `razvoj2`) in se v `main` združijo prek pull requesta.

## Avtor

Hušidić Merih
