# uvozimo ustrezne podatke za povezavo
import auth
auth.db = "sem2018_nejcc"

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki
import hashlib # računanje MD5 kriptografski hash za gesla
import csv

def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

# ustvari tabele za naso stran
def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE clan (
	id INTEGER PRIMARY KEY,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL,
	naslov TEXT NOT NULL,
	bio TEXT NOT NULL
);

CREATE TYPE spol AS ENUM ('moški', 'ženska', 'drugo');

CREATE TABLE uporabnik (
	id SERIAL PRIMARY KEY,
	uporabnisko_ime TEXT NOT NULL UNIQUE,
	geslo TEXT NOT NULL,
	stanje INTEGER DEFAULT 0,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL,
	spol_uporabnika spol NOT NULL,
	email TEXT NOT NULL,
	gru BOOLEAN DEFAULT false,
	admin BOOLEAN DEFAULT false
);


CREATE TABLE zanr(
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL
);


CREATE TABLE album(
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	opis TEXT NOT NULL,
	cena INTEGER NOT NULL
);


CREATE TABLE pesem (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	dolzina INTERVAL NOT NULL,
	izdan DATE NOT NULL,
	zanr INTEGER NOT NULL REFERENCES zanr(id),
	cena INTEGER NOT NULL
);

CREATE TABLE kupil_pesem (
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    uporabnikID SERIAL NOT NULL REFERENCES uporabnik(id),
    CONSTRAINT PK_kupil_pesem PRIMARY KEY (pesemID, uporabnikID)
);

CREATE TABLE kupil_album (
    albumID SERIAL NOT NULL REFERENCES album(id),
    uporabnikID SERIAL NOT NULL REFERENCES uporabnik(id),
    CONSTRAINT PK_kupil_album PRIMARY KEY (albumID, uporabnikID)
);

CREATE TABLE avtor_pesmi (
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    clanID SERIAL NOT NULL REFERENCES clan(id),
    CONSTRAINT PK_avtor_pesem PRIMARY KEY (pesemID, clanID)
);

CREATE TABLE avtor_besedila_pesmi (
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    clanID SERIAL NOT NULL REFERENCES clan(id),
    CONSTRAINT PK_avtor_besedila_pesmi PRIMARY KEY (pesemID, clanID)
);


CREATE TABLE album_pesem (
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    albumID SERIAL NOT NULL REFERENCES album(id),
    CONSTRAINT PK_albumpesmem PRIMARY KEY (pesemID, albumID)
);

CREATE TABLE tip_lit_dela(
    id SERIAL PRIMARY KEY,
    naslov TEXT NOT NULL
);

CREATE TABLE lit_delo (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	zaloznik TEXT NOT NULL,
	tip INTEGER NOT NULL REFERENCES tip_lit_dela(id)
);

CREATE TABLE avtor_lit_dela (
    litdeloID SERIAL NOT NULL REFERENCES lit_delo(id),
    clanID SERIAL NOT NULL REFERENCES clan(id),
    CONSTRAINT PK_avtor_lit_dela PRIMARY KEY (litdeloID, clanID)
);

CREATE TABLE tip_av_dela(
    id SERIAL PRIMARY KEY,
    naslov TEXT NOT NULL
);

CREATE TABLE avdio_video (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	tip INTEGER NOT NULL REFERENCES tip_av_dela(id)
);

CREATE TABLE avtor_av_dela (
    avdeloID SERIAL NOT NULL REFERENCES avdio_video(id),
    clanID SERIAL NOT NULL REFERENCES clan(id),
    CONSTRAINT PK_avtor_av_dela PRIMARY KEY (avdeloID, clanID)
);

CREATE TABLE dogodek (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	datum DATE NOT NULL,
	tip TEXT NOT NULL
);

CREATE TABLE izvedene_pesmi (
    dogodekID SERIAL NOT NULL REFERENCES dogodek(id),
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    CONSTRAINT PK_izvedene_pesmi PRIMARY KEY (dogodekID, pesemID)
);

CREATE TABLE izvedena_av_dela (
    dogodekID SERIAL NOT NULL REFERENCES dogodek(id),
    avdeloID SERIAL NOT NULL REFERENCES avdio_video(id),
    CONSTRAINT PK_izvedena_av_dela PRIMARY KEY (dogodekID, avdeloID)
);

CREATE TABLE izvedena_lit_dela (
    dogodekID SERIAL NOT NULL REFERENCES dogodek(id),
    litdeloID SERIAL NOT NULL REFERENCES lit_delo(id),
    CONSTRAINT PK_izvedena_lit_dela PRIMARY KEY (dogodekID, litdeloID)
);

CREATE TABLE udelezba_dogodka (
    dogodekID SERIAL NOT NULL REFERENCES dogodek(id),
    uporabnikID SERIAL NOT NULL REFERENCES uporabnik(id),
    CONSTRAINT PK_udelezba_dogodka PRIMARY KEY (dogodekID, uporabnikID)
);

GRANT ALL ON ALL TABLES IN SCHEMA public TO nejcc;
GRANT ALL ON ALL TABLES IN SCHEMA public TO martinm;
GRANT CONNECT ON DATABASE sem2018_martinm TO nejcc;
GRANT CONNECT ON DATABASE sem2018_nejcc TO martinm;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO nejcc;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO martinm;
GRANT CONNECT ON DATABASE sem2018_martinm TO javnost;
GRANT CONNECT ON DATABASE sem2018_nejcc TO javnost;
GRANT SELECT, UPDATE, INSERT ON ALL TABLES IN SCHEMA public TO javnost;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO javnost;
    """)
    conn.commit()

# izbrise tabele
def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE IF EXISTS clan CASCADE;
        DROP TABLE IF EXISTS uporabnik CASCADE;
        DROP TABLE IF EXISTS avdio_video CASCADE;
        DROP TABLE IF EXISTS pesem CASCADE;
        DROP TABLE IF EXISTS album CASCADE;
        DROP TABLE IF EXISTS lit_delo CASCADE;
        DROP TABLE IF EXISTS dogodek CASCADE;
        DROP TABLE IF EXISTS zanr CASCADE;
        DROP TABLE IF EXISTS album_pesem CASCADE;
        DROP TABLE IF EXISTS avtor_av_dela CASCADE;
        DROP TABLE IF EXISTS avtor_besedila_pesmi CASCADE;
        DROP TABLE IF EXISTS avtor_lit_dela CASCADE;
        DROP TABLE IF EXISTS avtor_pesmi CASCADE;
        DROP TABLE IF EXISTS izvedene_pesmi CASCADE;
        DROP TABLE IF EXISTS izvedena_av_dela CASCADE;
        DROP TABLE IF EXISTS izvedena_lit_dela CASCADE;
        DROP TABLE IF EXISTS tip_lit_dela CASCADE;
        DROP TABLE IF EXISTS tip_av_dela CASCADE;
        DROP TABLE IF EXISTS kupil_pesem CASCADE;
        DROP TABLE IF EXISTS kupil_album CASCADE;
        DROP TABLE IF EXISTS udelezba_dogodka CASCADE;
        DROP TYPE IF EXISTS spol CASCADE;
    """)
    conn.commit()

# uvozi nekaj osnovnih podatkov v tabele
def uvozi_podatke():
    cur.execute("""
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (42, 'Marko', 'Miocic', to_date('23-04-1996', 'dd-mm-yyyy'), 'Domzale', 'Hodil na gimnazijo Bežigrad.');
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (69, 'Martin', 'Molan', to_date('15-05-1996', 'dd-mm-yyyy'), 'Grosuplje', 'Hodil na gimnazijo Bežigrad.');
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (0, 'Nejc', 'Černe', to_date('21-09-1996', 'dd-mm-yyyy'), 'Ljubljana', 'Hodil na gimnazijo Bežigrad.');

                INSERT INTO zanr(naslov) VALUES ('indie');
                INSERT INTO zanr(naslov) VALUES ('pop');
                INSERT INTO zanr(naslov) VALUES ('elektro');

                INSERT INTO album(naslov, izdan, opis, cena) VALUES ('Kdo ponareja?', to_date('13-05-2018', 'dd-mm-yyyy'), 'Kolektiv je s tem albumom vstopil na sceno.', 1000);
                INSERT INTO album(naslov, izdan, opis, cena) VALUES ('Kopija prvega albuma', to_date('23-06-2018', 'dd-mm-yyyy'), 'Kolektiv je kopiral svoj prvi album.', 900);

                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Zivim kot ponarejevalc', '2 minutes 7 seconds', to_date('21-10-2017', 'dd-mm-yyyy'), 2, 25);
                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Ponaredki', '2 minutes 14 seconds', to_date('21-12-2017', 'dd-mm-yyyy'), 2, 30);
                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Ponarejen svet', '2 minutes 38 seconds', to_date('15-01-2018', 'dd-mm-yyyy'), 2, 10);
                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Vrednost originala', '2 minutes 12 seconds', to_date('26-02-2018', 'dd-mm-yyyy'), 2, 10);
                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Banke znorijo', '1 minutes 25 seconds', to_date('11-03-2018', 'dd-mm-yyyy'), 3, 50);
                INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Sprosti se', '53 seconds', to_date('08-04-2018', 'dd-mm-yyyy'), 3, 80);

                INSERT INTO tip_lit_dela(naslov) VALUES ('drama');
                INSERT INTO tip_lit_dela(naslov) VALUES ('kratka zgodba');
                INSERT INTO tip_lit_dela(naslov) VALUES ('novela');
                INSERT INTO tip_lit_dela(naslov) VALUES ('filozofski esej');

                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('25', to_date('21-11-2017', 'dd-mm-yyyy'), 'Fake Wizard Productions', 1);
                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('Soba', to_date('12-12-2017', 'dd-mm-yyyy'), 'Fake Wizard Productions', 2);
                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('Desno', to_date('19-01-2018', 'dd-mm-yyyy'), 'Fake Wizard Productions', 3);
                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('Parazit', to_date('25-02-2018', 'dd-mm-yyyy'), 'Fake Wizard Productions', 2);
                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('Zapor', to_date('10-03-2018', 'dd-mm-yyyy'), 'Fake Wizard Productions', 2);
                INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES ('Drzava', to_date('22-03-2016', 'dd-mm-yyyy'), 'Fake Wizard Productions', 4);

                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (1, 0);
                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (2, 0);
                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (3, 0);
                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (4, 0);
                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (5, 0);
                INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (6, 69);

                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (1, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (2, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (3, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (4, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (5, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (6, 0);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (1, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (2, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (3, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (4, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (5, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (6, 69);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (1, 42);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (2, 42);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (3, 42);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (4, 42);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (5, 42);
                INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (6, 42);

                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (1, 0);
                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (2, 0);
                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (3, 0);
                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (4, 0);
                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (5, 0);
                INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (6, 0);

                INSERT INTO album_pesem(pesemid, albumid) VALUES (1, 1);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (2, 1);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (3, 1);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (4, 1);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (5, 1);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (6, 1);

                INSERT INTO album_pesem(pesemid, albumid) VALUES (1, 2);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (2, 2);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (3, 2);
                INSERT INTO album_pesem(pesemid, albumid) VALUES (4, 2);

                INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika, email, admin) VALUES ('Mozi111','"""+password_md5('123')+"""', 999, 'Nejc', 'Černe', to_date('21-09-1996', 'dd-mm-yyyy'), 'moški', 'splintercell.savage@gmail.com',true);
                INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika, email) VALUES ('Yonstopir','""" +password_md5('Ooteebae4ai')+"""', 100, 'Lucy', 'Boyle', to_date('25-10-1996', 'dd-mm-yyyy'), 'ženska', 'lucy.boyle@gmail.com');
                INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika, email) VALUES ('Thimpturaw','""" +password_md5('Ri8Ueyoo3oT')+"""', 225, 'Eve', 'Fletcher', to_date('03-05-1996', 'dd-mm-yyyy'), 'ženska', 'eve.fletcher@gmail.com');
                INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika, email) VALUES ('Whistless','""" +password_md5('AhC0ahboog')+"""', 35, 'Isabella', 'Atkins', to_date('11-11-1996', 'dd-mm-yyyy'), 'ženska', 'isabella.atkins@gmail.com');

                INSERT INTO dogodek(naslov, datum, tip) VALUES ('Predstavitveni koncert', to_date('13-06-2018', 'dd-mm-yyyy'), 'koncert');
                INSERT INTO dogodek(naslov, datum, tip) VALUES ('Zabranjeno pušenje', to_date('31-01-1984', 'dd-mm-yyyy'), 'Veliki koncert');
                INSERT INTO dogodek(naslov, datum, tip) VALUES ('Novi klinci', to_date('06-05-2018', 'dd-mm-yyyy'), 'Mikro koncert');
                INSERT INTO dogodek(naslov, datum, tip) VALUES ('Bližnja prihodnost', to_date('20-06-2018', 'dd-mm-yyyy'), 'koncertino');
                INSERT INTO dogodek(naslov, datum, tip) VALUES ('V daljavi', to_date('21-09-2020', 'dd-mm-yyyy'), 'Koncert upanja');

                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (1, 1);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (1, 2);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (1, 3);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (1, 4);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (1, 5);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (2, 3);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (2, 1);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (2, 5);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (3, 2);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (4, 3);
                INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (5, 4);

                INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (3, 1);
                INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (4, 2);
                INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (5, 3);
                INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (4, 4);
                INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (3, 5);

                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (1, 3);
                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (1, 4);
                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (2, 3);
                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (3, 4);
                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (3, 3);
                INSERT INTO kupil_pesem(pesemid, uporabnikid) VALUES (5, 4);

                INSERT INTO udelezba_dogodka(dogodekid, uporabnikid) VALUES (1, 1);
                INSERT INTO udelezba_dogodka(dogodekid, uporabnikid) VALUES (1, 2);
                INSERT INTO udelezba_dogodka(dogodekid, uporabnikid) VALUES (1, 3);
                INSERT INTO udelezba_dogodka(dogodekid, uporabnikid) VALUES (1, 4);
            """)
    conn.commit()

# uredi pravice za dostop do baze
def pravice():
    cur.execute("""
        GRANT ALL ON ALL TABLES IN SCHEMA public TO martinm;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO martinm;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO nejcc;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO nejcc;
        GRANT CONNECT ON DATABASE sem2018_martinm TO nejcc;
        GRANT ALL ON SCHEMA public TO nejcc;
        GRANT SELECT, UPDATE, INSERT ON ALL TABLES IN SCHEMA public TO javnost;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO javnost;
    """)
    conn.commit()

conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
