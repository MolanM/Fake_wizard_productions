#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottle import *

# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

static_dir = "./static"
# odkomentiraj, če želiš sporočila o napakah
# debug(True)

@route("/")
def main():
    redirect("/clani/")

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@get('/clani/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('residents.html', clani=cur)

@get('/gallery/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('gallery.html', clani=cur)

@get('/index/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('index.html', clani=cur)

@get('/news/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('news.html', clani=cur)

@get('/parties/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('parties.html', clani=cur)

@get('/contacts/')
def uporabnik():
    x = 0
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
    return template('contacts.html', x=x, napaka = "Vse OK", uporabniki=cur)

@post('/contacts/')
def uporabnik():
    x = 0
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
    #spremenljivko smo shranili v znesek
    UporabniskoIme = request.forms.uporabniskoime
    Geslo = request.forms.geslo
    Stanje = request.forms.stanje
    Ime = request.forms.ime
    Priimek = request.forms.priimek
    Rojstvo = request.forms.rojstvo
    Spol = request.forms.spol
    if UporabniskoIme != "":
        try:
            #PraviRacun=int(RacunPython)
            cur.execute("INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika) VALUES (%s, %s, %s, %s, %s, to_date(%s, 'yyyy-mm-dd'), %s);",
                        [UporabniskoIme, Geslo, Stanje, Ime, Priimek, Rojstvo, Spol])
        except:
            return template('contacts.html', x=x, napaka = "Napaka pri dodajanju uporabnika",uporabniki=cur)
        redirect('/contacts/')
    return template('contacts.html', x=x, napaka = "Vse OK", uporabniki=cur)


# @get('/uporabniki/:x/')
# def transakcije(x):
#     cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
#     return template('uporabniki.html', x=x, napaka = "Vse OK", uporabniki=cur)

#@post('/uporabniki/:x/')
#def transakcijePost(x):
#    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
#    #spremenljivko smo shranili v znesek
#    ZnesekPython = request.forms.znesek
#    RacunPython = request.forms.racun
#    OpisPython = request.forms.opis
#    print(ZnesekPython)
#    #da nas preusmeri, če je vse v redu
#    try:
#        PraviRacun=int(RacunPython) #ce se to da
#        cur.execute("INSERT INTO transkacija (znesek, racun, opis) VALUES FROM (%s, %s, %s)", #[ZnesekPython, PraviRacun, OpisPython])
#    except: #če javi python napako
#        return template('uporabniki.html', x=x, napaka = "To ni stevilka",transakcije=cur)
#    redirect('/uporabniki/'+x+'/')
#    return template('uporabniki.html', x=x, napaka = "Vse OK", transakcije=cur)




######################################################################
# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

# poženemo strežnik na portu 8080, glej http://localhost:8080/
run(host='localhost', port=8080)
