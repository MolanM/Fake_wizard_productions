# uvozimo ustrezne podatke za povezavo
import auth
auth.db = "sem2018_%s" % auth.user

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv

def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE clan (
	id INTEGER PRIMARY KEY,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL,
	naslov TEXT,
	bio TEXT
);


CREATE TABLE uporabnik (
	id SERIAL PRIMARY KEY,
	uporabnisko_ime TEXT NOT NULL UNIQUE,
	geslo TEXT NOT NULL,
	stanje INTEGER DEFAULT 0,
	ime TEXT NOT NULL,
	priimek TEXT NOT NULL,
	rojstvo DATE NOT NULL,
	spol TEXT NOT NULL,
	gru BOOLEAN DEFAULT false
);


CREATE TABLE zanr(
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL
);


CREATE TABLE album(
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	opis TEXT,
	cena INTEGER
);


CREATE TABLE pesem (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	dolzina INTEGER NOT NULL,
	izdan DATE NOT NULL,
	zanr INTEGER NOT NULL REFERENCES zanr(id),
	cena INTEGER
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


CREATE TABLE albumpesem (
    pesemID SERIAL NOT NULL REFERENCES pesem(id),
    albumID SERIAL NOT NULL REFERENCES album(id),
    CONSTRAINT PK_albumpesmem PRIMARY KEY (pesemID, albumID)
);


CREATE TABLE lit_delo (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	zaloznik TEXT,
	tip TEXT NOT NULL
);

CREATE TABLE avtor_lit_dela (
    litdeloID SERIAL NOT NULL REFERENCES lit_delo(id),
    clanID SERIAL NOT NULL REFERENCES clan(id),
    CONSTRAINT PK_avtor_lit_dela PRIMARY KEY (litdeloID, clanID)
);

CREATE TABLE avdio_video (
	id SERIAL PRIMARY KEY,
	naslov TEXT NOT NULL,
	izdan DATE NOT NULL,
	tip TEXT NOT NULL
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
    """)
    conn.commit()

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
        DROP TABLE IF EXISTS albumpesem CASCADE;
        DROP TABLE IF EXISTS avtor_av_dela CASCADE;
        DROP TABLE IF EXISTS avtor_besedila_pesmi CASCADE;
        DROP TABLE IF EXISTS avtor_lit_dela CASCADE;
        DROP TABLE IF EXISTS avtor_pesmi CASCADE;
        DROP TABLE IF EXISTS izvedene_pesmi CASCADE;
    """)
    conn.commit()
#verjetno ne bova uporabljala

def uvozi_podatke():
    cur.execute("""
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (42, 'Marko', 'Miocic', to_date('23-04-1996', 'dd-mm-yyyy'), 'Domzale', 'Hodil na gimnazijo Bežigrad.');
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (69, 'Martin', 'Molan', to_date('15-05-1996', 'dd-mm-yyyy'), 'Grosuplje', 'Hodil na gimnazijo Bežigrad.');
                INSERT INTO clan(id, ime, priimek, rojstvo, naslov, bio) VALUES (0, 'Nejc', 'Černe', to_date('21-09-1996', 'dd-mm-yyyy'), 'Ljubljana', 'Hodil na gimnazijo Bežigrad.');

                INSERT INTO zanr(naslov) VALUES ('indie');
                INSERT INTO zanr(naslov) VALUES ('pop');
                INSERT INTO zanr(naslov) VALUES ('punk');

                INSERT INTO album(naslov, izdan, opis, cena) VALUES ('Kdo ponareja?', to_date('13-05-2018', 'dd-mm-yyyy'), 'Kolektiv je s tem albumom vstopil na sceno.', 0);

                --INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES ('Zivim kot ponarejevalc', 3, to_date('21-10-2017', 'dd-mm-yyyy'), 1, 0);
            """)
    conn.commit()



    
 #def uvozi_podatke():
 #   with open("obcine.csv") as f:
 #       rd = csv.reader(f)
 #       next(rd) # izpusti naslovno vrstico
 #       for r in rd:
 #           r = [None if x in ('', '-') else x for x in r]
 #           cur.execute("""
 #               INSERT INTO obcina
 #               (ime, povrsina, prebivalstvo, gostota, naselja,
 #                ustanovitev, pokrajina, stat_regija, odcepitev)
 #               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
 #               RETURNING id
 #           """, r)
 #           rid, = cur.fetchone()
 #           print("Uvožena občina %s z ID-jem %d" % (r[0], rid))
 #   conn.commit()


conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
