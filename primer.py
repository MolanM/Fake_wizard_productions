#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottle import *

# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

# odkomentiraj, če želiš sporočila o napakah
# debug(True)

@get('/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('clani.html', clani=cur)

@get('/uporabniki/:x/')
def transakcije(x):
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
    return template('uporabniki.html', x=x, napaka = "Vse OK", transakcije=cur)

@post('/uporabniki/:x/')
def transakcijePost(x):
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
    #spremenljivko smo shranili v znesek
    ZnesekPython = request.forms.znesek
    RacunPython = request.forms.racun
    OpisPython = request.forms.opis
    print(ZnesekPython)
    #da nas preusmeri, če je vse v redu
    try:
        PraviRacun=int(RacunPython) #ce se to da
        cur.execute("INSERT INTO transkacija (znesek, racun, opis) VALUES FROM (%s, %s, %s)", [ZnesekPython, PraviRacun, OpisPython])
    except: #če javi python napako
        return template('uporabniki.html', x=x, napaka = "To ni stevilka",transakcije=cur)
    redirect('/uporabniki/'+x+'/')
    return template('uporabniki.html', x=x, napaka = "Vse OK", transakcije=cur)




######################################################################
# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

# poženemo strežnik na portu 8080, glej http://localhost:8080/
run(host='localhost', port=8080)
