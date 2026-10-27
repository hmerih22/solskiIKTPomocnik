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


## Struktura repozitorija

```
├── README.md
├── .gitignore
├── frontend/      # uporabniški vmesnik (Jinja predloge, CSS) – v pripravi
├── backend/       # Flask aplikacija – v pripravi
└── docs/          # dokumentacija, wireframes in ADR
```

## Način dela (GitHub Flow)

Veja `main` je zaščitena. Vse spremembe nastanejo na ločeni veji (npr. `feature/razvoj`) in se v `main` združijo prek pull requesta.

```bash
git switch -c feature/ime-spremembe
# ... spremembe ...
git add .
git commit -m "Opis spremembe"
git push -u origin feature/ime-spremembe
# na GitHubu odpri pull request v main
```

## Avtor

Hušidić Merih
