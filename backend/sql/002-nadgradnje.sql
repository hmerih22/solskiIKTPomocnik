-- =====================================================================
-- Šolski IKT pomočnik – razširitev sheme za nadgradnje F08–F11
-- Izvede se za 001-schema.sql. Tudi ta skripta ne vsebuje USE.
-- =====================================================================

-- ---------------------------------------------------------------------
-- F08: dejanski prevzem in vračilo opreme
-- ---------------------------------------------------------------------
ALTER TABLE rezervacija
    ADD COLUMN prevzeta_ob DATETIME NULL,
    ADD COLUMN vrnjena_ob  DATETIME NULL,
    -- Vračilo je mogoče samo po prevzemu.
    ADD CONSTRAINT chk_rezervacija_vracilo CHECK (vrnjena_ob IS NULL OR prevzeta_ob IS NOT NULL),
    -- Pregled izposojene opreme.
    ADD INDEX ix_rezervacija_prevzem (prevzeta_ob, vrnjena_ob);

-- ---------------------------------------------------------------------
-- F09: komentarji pri prijavi
-- ---------------------------------------------------------------------
CREATE TABLE komentar_prijave (
    id            INT      NOT NULL AUTO_INCREMENT,
    prijava_id    INT      NOT NULL,
    avtor_id      INT      NOT NULL,
    besedilo      TEXT     NOT NULL,
    ustvarjen_ob  DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP()),

    CONSTRAINT pk_komentar_prijave PRIMARY KEY (id),
    CONSTRAINT fk_komentar_prijava FOREIGN KEY (prijava_id) REFERENCES prijava_tezave (id),
    CONSTRAINT fk_komentar_avtor FOREIGN KEY (avtor_id) REFERENCES uporabnik (id),
    CONSTRAINT chk_komentar_besedilo CHECK (TRIM(besedilo) <> ''),

    INDEX ix_komentar_prijava_cas (prijava_id, ustvarjen_ob)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- F10: priponke pri prijavi
-- Datoteka je shranjena na disku pod naključnim imenom (shranjeno_ime);
-- izvirno ime se uporablja samo za prikaz in prenos.
-- ---------------------------------------------------------------------
CREATE TABLE priponka_prijave (
    id             INT          NOT NULL AUTO_INCREMENT,
    prijava_id     INT          NOT NULL,
    izvirno_ime    VARCHAR(255) NOT NULL,
    shranjeno_ime  VARCHAR(64)  NOT NULL,
    vrsta          ENUM('image/jpeg', 'image/png', 'application/pdf') NOT NULL,
    velikost       INT          NOT NULL,
    ustvarjena_ob  DATETIME     NOT NULL DEFAULT (UTC_TIMESTAMP()),

    CONSTRAINT pk_priponka_prijave PRIMARY KEY (id),
    CONSTRAINT uq_priponka_shranjeno_ime UNIQUE (shranjeno_ime),
    CONSTRAINT fk_priponka_prijava FOREIGN KEY (prijava_id) REFERENCES prijava_tezave (id),
    -- Največ 5 MiB na datoteko.
    CONSTRAINT chk_priponka_velikost CHECK (velikost > 0 AND velikost <= 5242880)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- F11: evidenca e-poštnih obvestil
-- Vsako sproženo obvestilo se zabeleži; ob napaki pri pošiljanju se
-- shrani razlog, uspešno shranjena operacija pa ostane veljavna.
-- ---------------------------------------------------------------------
CREATE TABLE obvestilo (
    id           INT          NOT NULL AUTO_INCREMENT,
    prejemnik    VARCHAR(254) NOT NULL,
    zadeva       VARCHAR(200) NOT NULL,
    besedilo     TEXT         NOT NULL,
    ustvarjeno_ob DATETIME    NOT NULL DEFAULT (UTC_TIMESTAMP()),
    status       ENUM('poslano', 'samo_zabelezeno', 'napaka') NOT NULL,
    napaka       TEXT         NULL,

    CONSTRAINT pk_obvestilo PRIMARY KEY (id),
    INDEX ix_obvestilo_cas (ustvarjeno_ob)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
