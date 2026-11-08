-- =====================================================================
-- Priprava baze in uporabnika za aplikacijo (izvede razvijalec kot root).
--
-- 1. Kopiraj to datoteko v backend/sql/local-priprava.sql
--    (datoteke local-*.sql so v .gitignore in se ne shranijo v Git).
-- 2. GESLO_APLIKACIJE zamenjaj z geslom, ki ga vpišeš tudi v .env (DB_PASSWORD).
-- 3. V korenski mapi projekta zaženi:
--    & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 -e "source backend/sql/local-priprava.sql"
--
-- POZOR: skripta izbriše in na novo ustvari obe bazi (vsi podatki se izgubijo).
-- =====================================================================

DROP DATABASE IF EXISTS solski_ikt;
DROP DATABASE IF EXISTS solski_ikt_test;

CREATE DATABASE solski_ikt CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE solski_ikt_test CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Uporabnik aplikacije se lahko poveže samo z lokalnega računalnika.
DROP USER IF EXISTS 'solski_ikt_app'@'localhost';
CREATE USER 'solski_ikt_app'@'localhost' IDENTIFIED BY 'GESLO_APLIKACIJE';

-- Glavna baza: aplikacija sme samo brati in spreminjati podatke, ne pa sheme.
GRANT SELECT, INSERT, UPDATE, DELETE ON solski_ikt.* TO 'solski_ikt_app'@'localhost';

-- Testna baza: testi tabele ustvarjajo in brišejo, zato potrebujejo vse pravice.
GRANT ALL PRIVILEGES ON solski_ikt_test.* TO 'solski_ikt_app'@'localhost';

-- Shema v glavni bazi.
USE solski_ikt;
source backend/sql/001-schema.sql
