# Šolski IKT pomočnik

Spletna aplikacija za **rezervacijo skupne šolske IKT-opreme** (prenosniki, projektorji, kompleti tablic) ter **prijavo in obravnavo tehničnih težav** znotraj ene šole.

Učitelji preverijo razpoložljivost opreme, jo rezervirajo brez prekrivanja terminov in prijavijo težave na opremi ali v učilnici. IKT skrbnik prevzema in rešuje prijave ter označuje nedelujočo opremo, administrator pa upravlja uporabniške račune, učilnice in evidenco opreme.

Aplikacija vključuje celoten MVP (F01–F07) in vse nadgradnje (F08–F12): prevzem in vračilo opreme, komentarje, priponke, e-poštna obvestila in statistiko.

## Namestitev in zagon (Windows PowerShell)

```powershell
# 1. Virtualno okolje in knjižnice
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 2. Nastavitve: kopiraj .env.example v .env in izpolni SECRET_KEY ter DB_PASSWORD
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # vrednost za SECRET_KEY

# 3. Baza: kopiraj pripravo, vanjo vpiši isto geslo kot DB_PASSWORD v .env, nato jo izvedi kot root
Copy-Item backend\sql\000-priprava.example.sql backend\sql\local-priprava.sql
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 -e "source backend/sql/local-priprava.sql"

# 4. Prvi administrator ALI demo podatki (5 uporabnikov z geslom demo1234)
flask --app backend/app create-admin
flask --app backend/app demo-podatki

# 5. Zagon
flask --app backend/app run --debug
```

Aplikacija je dostopna na <http://127.0.0.1:5000>. Z demo podatki se lahko prijaviš kot `admin@sola.si`, `skrbnik@sola.si` ali `ucitelj@sola.si` (geslo `demo1234`).

Skripta `local-priprava.sql` izbriše in na novo ustvari bazi `solski_ikt` in `solski_ikt_test` ter ustvari uporabnika `solski_ikt_app`. Datoteke `local-*.sql` so v `.gitignore`, ker vsebujejo geslo.

### Testi

```powershell
python -m pytest
```

Testi z bazo uporabljajo ločeno bazo `solski_ikt_test` in jo pred vsakim testom izpraznijo; glavne baze ne spreminjajo. Če baza ni dosegljiva, se ti testi preskočijo (razlog izpiše `python -m pytest -rs`). Med testi sta tudi preverjanji sočasne rezervacije in sočasnega prevzema prijave na pravi bazi MySQL.

## Zgradba kode

| Pot | Vsebina |
| --- | --- |
| `backend/app/__init__.py` | `create_app`: nastavitve, registracija modulov, filtri predlog, strani z napakami |
| `backend/app/auth.py` | Prijava, odjava, nalaganje uporabnika ob vsaki zahtevi, dekorator `zahteva_vlogo` |
| `backend/app/oprema.py`, `rezervacije.py`, `prijave.py`, `admin.py`, `statistika.py` | Poti (Flask blueprints): preberejo obrazec, pokličejo storitev, izrišejo predlogo |
| `backend/app/services/` | Poslovna pravila in transakcije (prekrivanje rezervacij, prevzem prijave, pravice) |
| `backend/app/repositories/` | Vse SQL-poizvedbe s parametri `%s` |
| `backend/app/db.py` | Povezava na zahtevo, `transakcija()` |
| `backend/app/cas.py` | Pretvorba med UTC (baza) in Europe/Ljubljana (prikaz) |
| `backend/app/obrazci.py` | Obrazci Flask-WTF z zaščito CSRF |
| `backend/app/cli.py` | Ukaza `create-admin` in `demo-podatki` |
| `backend/sql/` | `001-schema.sql` (MVP), `002-nadgradnje.sql` (F08–F11) |
| `frontend/templates/`, `frontend/static/` | Jinja predloge in CSS |

Pot zahteve: **pot** (npr. `rezervacije.py`) → **storitev** (`services/rezervacije.py`, preveri pravila in pravice) → **repozitorij** (`repositories/rezervacije.py`, SQL) → baza.

## Uporabljene tehnologije

| Področje | Tehnologije |
| --- | --- |
| Zaledje (backend) | Python, Flask |
| Uporabniški vmesnik (frontend) | HTML, CSS, Jinja predloge (strežniško upodabljanje) |
| Podatkovna baza | MySQL 8.4 (InnoDB, `utf8mb4`) |
| Dostop do baze | MySQL Connector/Python, parametrizirane SQL-poizvedbe |
| Avtentikacija | Flask-Login, Werkzeug (zgoščevanje gesel) |
| Obrazci in CSRF | Flask-WTF |
| Nastavitve | okoljske spremenljivke, python-dotenv |
| Testiranje | pytest, Flask testni odjemalec |
| Verzije kode | Git, GitHub (GitHub Flow) |

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


## Struktura repozitorija

```
├── README.md
├── .gitignore
├── frontend/      # templates/ (Jinja predloge), static/ (CSS)
├── backend/       # app/ (Flask aplikacija), sql/ (shema baze), tests/
└── docs/          # dokumentacija, wireframes in ADR
```

## Način dela (GitHub Flow)

Veja `main` je zaščitena. Vse spremembe nastanejo na razvojni veji `razvoj` in se v `main` združijo prek pull requesta.

```bash
git switch razvoj
# ... spremembe ...
git add .
git commit -m "Opis spremembe"
git push -u origin razvoj
# na GitHubu odpri pull request iz razvoj v main
```

## Avtor

Hušidić Merih FNM
