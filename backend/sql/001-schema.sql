-- =====================================================================
-- Šolski IKT pomočnik – začetna shema baze (MySQL 8.4, InnoDB, utf8mb4)
-- Tabele: uporabnik, ucilnica, oprema, rezervacija, prijava_tezave
--
-- Skripta ne vsebuje USE, zato jo lahko izvedemo na glavni bazi
-- (solski_ikt) ali na testni bazi (solski_ikt_test).
-- Vsi časi se hranijo v UTC.
--
-- Tuji ključi uporabljajo privzeto pravilo RESTRICT: povezanih zapisov ni
-- mogoče izbrisati, MySQL pa zato dovoli CHECK omejitve na teh stolpcih.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Uporabnik
-- ---------------------------------------------------------------------
CREATE TABLE uporabnik (
    id            INT          NOT NULL AUTO_INCREMENT,
    ime           VARCHAR(100) NOT NULL,
    priimek       VARCHAR(100) NOT NULL,
    email         VARCHAR(254) NOT NULL,
    geslo_hash    VARCHAR(255) NOT NULL,
    vloga         ENUM('ucitelj', 'ikt_skrbnik', 'administrator') NOT NULL,
    aktiven       BOOLEAN      NOT NULL DEFAULT TRUE,
    ustvarjen_ob  DATETIME     NOT NULL DEFAULT (UTC_TIMESTAMP()),

    CONSTRAINT pk_uporabnik PRIMARY KEY (id),
    CONSTRAINT uq_uporabnik_email UNIQUE (email),
    CONSTRAINT chk_uporabnik_ime CHECK (TRIM(ime) <> ''),
    CONSTRAINT chk_uporabnik_priimek CHECK (TRIM(priimek) <> ''),
    CONSTRAINT chk_uporabnik_email CHECK (TRIM(email) <> '')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 2. Učilnica
-- ---------------------------------------------------------------------
CREATE TABLE ucilnica (
    id      INT          NOT NULL AUTO_INCREMENT,
    oznaka  VARCHAR(30)  NOT NULL,
    naziv   VARCHAR(100) NOT NULL,
    opis    TEXT         NULL,

    CONSTRAINT pk_ucilnica PRIMARY KEY (id),
    CONSTRAINT uq_ucilnica_oznaka UNIQUE (oznaka),
    CONSTRAINT chk_ucilnica_oznaka CHECK (TRIM(oznaka) <> ''),
    CONSTRAINT chk_ucilnica_naziv CHECK (TRIM(naziv) <> '')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 3. Oprema
-- ---------------------------------------------------------------------
CREATE TABLE oprema (
    id                  INT          NOT NULL AUTO_INCREMENT,
    naziv               VARCHAR(150) NOT NULL,
    inventarna_stevilka VARCHAR(50)  NOT NULL,
    vrsta               VARCHAR(50)  NOT NULL,
    opis                TEXT         NULL,
    stanje              ENUM('uporabna', 'nedelujoca') NOT NULL DEFAULT 'uporabna',
    ucilnica_id         INT          NOT NULL,

    CONSTRAINT pk_oprema PRIMARY KEY (id),
    CONSTRAINT uq_oprema_inventarna_stevilka UNIQUE (inventarna_stevilka),
    CONSTRAINT fk_oprema_ucilnica FOREIGN KEY (ucilnica_id) REFERENCES ucilnica (id),
    CONSTRAINT chk_oprema_naziv CHECK (TRIM(naziv) <> ''),
    CONSTRAINT chk_oprema_inventarna_stevilka CHECK (TRIM(inventarna_stevilka) <> ''),
    CONSTRAINT chk_oprema_vrsta CHECK (TRIM(vrsta) <> '')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 4. Rezervacija
-- ---------------------------------------------------------------------
CREATE TABLE rezervacija (
    id               INT      NOT NULL AUTO_INCREMENT,
    uporabnik_id     INT      NOT NULL,
    oprema_id        INT      NOT NULL,
    zacetek          DATETIME NOT NULL,
    konec            DATETIME NOT NULL,
    status           ENUM('aktivna', 'preklicana') NOT NULL DEFAULT 'aktivna',
    ustvarjena_ob    DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP()),
    preklicana_ob    DATETIME NULL,
    preklical_id     INT      NULL,
    razlog_preklica  TEXT     NULL,

    CONSTRAINT pk_rezervacija PRIMARY KEY (id),
    CONSTRAINT fk_rezervacija_uporabnik FOREIGN KEY (uporabnik_id) REFERENCES uporabnik (id),
    CONSTRAINT fk_rezervacija_oprema FOREIGN KEY (oprema_id) REFERENCES oprema (id),
    CONSTRAINT fk_rezervacija_preklical FOREIGN KEY (preklical_id) REFERENCES uporabnik (id),

    -- Začetek mora biti pred koncem (9.00–10.00 je veljavno, 10.00–10.00 ni).
    CONSTRAINT chk_rezervacija_termin CHECK (zacetek < konec),

    -- Aktivna rezervacija nima podatkov o preklicu; preklicana jih mora imeti.
    CONSTRAINT chk_rezervacija_preklic CHECK (
        (status = 'aktivna'
            AND preklicana_ob IS NULL AND preklical_id IS NULL AND razlog_preklica IS NULL)
        OR
        (status = 'preklicana'
            AND preklicana_ob IS NOT NULL AND preklical_id IS NOT NULL)
    ),

    -- Preverjanje razpoložljivosti opreme (prekrivanje terminov).
    INDEX ix_rezervacija_oprema_status_zacetek (oprema_id, status, zacetek),
    -- Seznam "Moje rezervacije".
    INDEX ix_rezervacija_uporabnik_zacetek (uporabnik_id, zacetek)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 5. Prijava težave
-- ---------------------------------------------------------------------
CREATE TABLE prijava_tezave (
    id              INT          NOT NULL AUTO_INCREMENT,
    prijavitelj_id  INT          NOT NULL,
    oprema_id       INT          NULL,
    ucilnica_id     INT          NULL,
    naslov          VARCHAR(150) NOT NULL,
    opis            TEXT         NOT NULL,
    status          ENUM('nova', 'v_obravnavi', 'resena') NOT NULL DEFAULT 'nova',
    skrbnik_id      INT          NULL,
    ustvarjena_ob   DATETIME     NOT NULL DEFAULT (UTC_TIMESTAMP()),
    prevzeta_ob     DATETIME     NULL,
    resitev         TEXT         NULL,
    resena_ob       DATETIME     NULL,

    CONSTRAINT pk_prijava_tezave PRIMARY KEY (id),
    CONSTRAINT fk_prijava_prijavitelj FOREIGN KEY (prijavitelj_id) REFERENCES uporabnik (id),
    CONSTRAINT fk_prijava_oprema FOREIGN KEY (oprema_id) REFERENCES oprema (id),
    CONSTRAINT fk_prijava_ucilnica FOREIGN KEY (ucilnica_id) REFERENCES ucilnica (id),
    CONSTRAINT fk_prijava_skrbnik FOREIGN KEY (skrbnik_id) REFERENCES uporabnik (id),

    CONSTRAINT chk_prijava_naslov CHECK (TRIM(naslov) <> ''),
    CONSTRAINT chk_prijava_opis CHECK (TRIM(opis) <> ''),

    -- Prijava mora biti povezana z opremo, učilnico ali obema.
    CONSTRAINT chk_prijava_oprema_ali_ucilnica CHECK (
        oprema_id IS NOT NULL OR ucilnica_id IS NOT NULL
    ),

    -- Zahtevani podatki glede na stanje prijave (tabela "Stanja prijave").
    CONSTRAINT chk_prijava_stanje CHECK (
        (status = 'nova'
            AND skrbnik_id IS NULL AND prevzeta_ob IS NULL
            AND resitev IS NULL AND resena_ob IS NULL)
        OR
        (status = 'v_obravnavi'
            AND skrbnik_id IS NOT NULL AND prevzeta_ob IS NOT NULL
            AND resena_ob IS NULL)
        OR
        (status = 'resena'
            AND skrbnik_id IS NOT NULL AND prevzeta_ob IS NOT NULL
            AND resitev IS NOT NULL AND TRIM(resitev) <> ''
            AND resena_ob IS NOT NULL)
    ),

    -- Seznam "Moje prijave".
    INDEX ix_prijava_prijavitelj_ustvarjena (prijavitelj_id, ustvarjena_ob),
    -- Pregled čakajočih prijav.
    INDEX ix_prijava_status_ustvarjena (status, ustvarjena_ob),
    -- Delo odgovornega skrbnika.
    INDEX ix_prijava_skrbnik_status (skrbnik_id, status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
