# Šolski IKT pomočnik

Spletna aplikacija za **rezervacijo skupne šolske IKT-opreme** (prenosniki, projektorji, kompleti tablic) ter **prijavo in obravnavo tehničnih težav** znotraj ene šole.

Učitelji preverijo razpoložljivost opreme, jo rezervirajo brez prekrivanja terminov in prijavijo težave na opremi ali v učilnici. IKT skrbnik prevzema in rešuje prijave ter označuje nedelujočo opremo, administrator pa upravlja uporabniške račune, učilnice in evidenco opreme.

> Projekt je trenutno v fazi zasnove. Direktorija `frontend/` in `backend/` sta pripravljena za implementacijo.

## Uporabljene tehnologije

| Področje | Tehnologija |
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

### Arhitekturne odločitve

| ADR | Odločitev |
| --- | --- |
| [0001](docs/adr/0001-python-in-flask-za-zaledje.md) | Python in Flask za zaledje |
| [0002](docs/adr/0002-enotna-aplikacija-z-locenimi-moduli.md) | Enotna aplikacija z ločenimi moduli |
| [0003](docs/adr/0003-strezniski-html-z-jinja-predlogami.md) | Strežniško sestavljen HTML z Jinja predlogami |
| [0004](docs/adr/0004-relacijska-baza-mysql.md) | Relacijska baza MySQL |
| [0005](docs/adr/0005-parametrizirane-sql-poizvedbe-brez-orm.md) | Parametrizirane SQL-poizvedbe brez ORM |
| [0006](docs/adr/0006-sejna-prijava-s-flask-login.md) | Sejna prijava s Flask-Login |
| [0007](docs/adr/0007-brez-javne-registracije.md) | Brez javne registracije |
| [0008](docs/adr/0008-transakcije-z-zaklepanjem-pri-kljucnih-operacijah.md) | Transakcije z zaklepanjem pri ključnih operacijah |

## Struktura repozitorija

```
├── README.md
├── .gitignore
├── frontend/      # uporabniški vmesnik (Jinja predloge, CSS) – v pripravi
├── backend/       # Flask aplikacija – v pripravi
└── docs/          # dokumentacija, wireframes in ADR
```

## Način dela (GitHub Flow)

Veja `main` je zaščitena. Vse spremembe nastanejo na ločeni veji (npr. `feature/rezervacije`) in se v `main` združijo prek pull requesta.

```bash
git switch -c feature/ime-spremembe
# ... spremembe ...
git add .
git commit -m "Opis spremembe"
git push -u origin feature/ime-spremembe
# na GitHubu odpri pull request v main
```

## Avtor

Husidić
