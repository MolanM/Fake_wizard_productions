#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottle import *

import hashlib # računanje MD5 kriptografski hash za gesla

# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

secret = "1094107m907oz982982i111"
static_dir = "./static"
# odkomentiraj, če želiš sporočila o napakah
# debug(True)

def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

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

@route('/contacts/')
def uporabnik():
    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
    return template('contacts.html', x=0, napaka = "Vse OK", uporabniki=cur)

@post('/contacts/')
def uporabnik():
    x = 0
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY stanje, id", [int(x)])
    #spremenljivko smo shranili v znesek
    UporabniskoIme = request.forms.uporabniskoime
    Geslo1 = request.forms.geslo1
    Geslo2 = request.forms.geslo2
    Stanje = request.forms.stanje
    Ime = request.forms.ime
    Priimek = request.forms.priimek
    Rojstvo = request.forms.rojstvo
    Spol = request.forms.spoli
    Slika = request.files.uploaded
    cur.execute("SELECT 1 FROM uporabnik WHERE uporabnisko_ime=%s", [UporabniskoIme])
    if cur.fetchone():
        # Uporabnik že obstaja
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('contacts.html', x=x, napaka = 'To uporabniško ime je že zavzeto', uporabniki=cur)
    elif not Geslo1 == Geslo2:
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('contacts.html', x=x, napaka = 'Gesli se ne ujemata', uporabniki=cur)
    elif Slika is None:
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('contacts.html', x=x, napaka = 'Niste dodali slike', uporabniki=cur)
    elif Slika is not None:
        name, ext = os.path.splitext(Slika.filename)
        if ext.lower() not in ('.png','.jpg','.jpeg'):
            cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
            return template('contacts.html', x=x, napaka = 'Slika ni v pravem formatu', uporabniki=cur)
        else:
            try:
                print("test1")
                print([str(UporabniskoIme), password_md5(Geslo1), int(Stanje), str(Ime), str(Priimek), str(Rojstvo), str(Spol)])
                #PraviRacun=int(RacunPython)    
                cur.execute("INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika) VALUES (%s, %s, %s, %s, %s, to_date(%s, 'yyyy-mm-dd'), %s);", [str(UporabniskoIme), password_md5(Geslo1), int(Stanje), str(Ime), str(Priimek), str(Rojstvo), str(Spol)])
                print("test2")
                cur.execute("SELECT last_value FROM uporabnik_id_seq") #ID novega uporabnika
                print("test3")
                userid=cur.fetchone()
                print(userid[0])
                filename = str(userid[0]) + ext
                print(filename)
                Slika.filename = filename
                save_path = os.path.join('static','images','uploads',filename) 
                Slika.save(save_path) # appends upload.filename automatically
                redirect('/contacts/')
            except:
                cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
                return template('contacts.html', x=x, napaka = "Napaka pri dodajanju uporabnika", uporabniki=cur)

@route("/user/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    cur.execute("SELECT * FROM uporabnik WHERE id = %s", [int(id)])
    Uporabnik = cur.fetchone()
    cur.execute("SELECT naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s", [int(id)])
    KupljenePesmi = []
    for (naslov,) in cur:
        KupljenePesmi.append(naslov)
    cur.execute("SELECT naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s", [int(id)])
    KupljeniAlbumi = []
    for (naslov,) in cur:
        KupljeniAlbumi.append(naslov)
    cur.execute("SELECT naslov FROM dogodek JOIN udelezba_dogodka ON dogodek.id = udelezba_dogodka.dogodekid WHERE uporabnikid = %s", [int(id)])
    UdelezeniDogodki = []
    for (naslov,) in cur:
        UdelezeniDogodki.append(naslov)
    # Prikažemo predlogo
    return template("user.html", uporabnik=Uporabnik, pesmi=KupljenePesmi, albumi=KupljeniAlbumi, dogodki=UdelezeniDogodki)

@post("/user/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    sprememba = request.forms.stanje
    cur.execute("UPDATE uporabnik SET stanje = stanje + %s WHERE id = %s", [sprememba, int(id)])
    redirect('/user/'+str(id)+'/')


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
