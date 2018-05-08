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

def get_user(auto_login = False):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Če ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka
    username = request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        cur.execute("SELECT uporabnisko_ime, ime, id FROM uporabnik WHERE uporabnisko_ime=%s",
                  [username])
        r = cur.fetchone()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/prijava/')
    else:
        return None

@route("/")
def main():
    redirect("/index/")

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@get('/clani/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('clani.html', clani=cur)

@get('/dogodki/')
def index():
    cur.execute("SELECT * FROM dogodek ORDER BY datum, id")
    return template('dogodki.html', dogodki=cur)

@get('/galerija/')
def index():
    return template('galerija.html')

@get('/index/')
def index():
    if get_user():
        (username_login, ime_login, id_user) = get_user()
    else:
        username_login = "tujec"
	
    """ Preberemo zadnje dogodke
    """
    cur.execute("SELECT * FROM dogodek WHERE datum <= now()::date ORDER BY datum DESC, id DESC LIMIT 5")
    cur1.execute("SELECT * FROM dogodek WHERE datum > now()::date ORDER BY datum ASC, id DESC LIMIT 5")
    
    return template('index.html', prijavljen_uporabnik=username_login, dogodki=cur, prihajajoci=cur1)

@get('/novice/')
def index():
    return template('novice.html')

@get('/kontakt/')
def index():
    return template('kontakt.html')

@get('/register/')
def index():
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('register.html', napaka="Vse OK", barva="green", clani=cur)

@get('/prijava/')
def index():
    if get_user():
        (username_login, ime_login, id_user) = get_user()
        return template('prijava.html', napaka="Ste že prijavljeni!", barva="red", prijavljen_uporabnik=username_login)
    else:
        return template('prijava.html', napaka="Vse OK", barva="green", prijavljen_uporabnik=None)

@get("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    response.delete_cookie('username', path='/', domain='localhost')
    redirect('/')

@post("/prijava/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    username = request.forms.uporabniskoime
    # Izračunamo MD5 has gesla, ki ga bomo spravili
    password = password_md5(request.forms.geslo)
    # Preverimo, ali se je uporabnik pravilno prijavil
    if username and password:
        cur.execute("SELECT 1 FROM uporabnik WHERE uporabnisko_ime=%s AND geslo=%s",
                  [username, password])
        if cur.fetchone() is None:
            # Username in geslo se ne ujemata
            return template("prijava.html",
                                   napaka="Uporabniško ime in geslo se ne ujemata", barva="red",
                                   username=username, prijavljen_uporabnik=None)
        else:
            # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
            response.set_cookie('username', username, path='/', secret=secret)
            redirect("/")
    else:
        return template("prijava.html",
                                   napaka="Nepravilna prijava", barva="red",
                                   username=username, prijavljen_uporabnik=None)

@get('/uporabniki/')
def uporabnik():
    query = dict(request.query)
    ORstring='''
        SELECT * FROM uporabnik
        WHERE 1=1\n'''
    parameters = [] #vektor parametrov za sql stavke
    try: test = query['search']
    except: query['search'] = ''
    if query['search'] != '':
        ORstring += '''AND (LOWER(uporabnisko_ime) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    ORstring += '''ORDER BY uporabnisko_ime'''
    cur.execute(ORstring,parameters)
    return template('uporabniki.html', x=0, napaka = "Vse OK", uporabniki=cur.fetchall())

@post('/register/')
def uporabnik():
    x = 0
    cur.execute("SELECT * FROM uporabnik WHERE stanje > %s ORDER BY uporabnisko_ime, stanje", [int(x)])
    #spremenljivko smo shranili v znesek
    UporabniskoIme = request.forms.uporabniskoime
    Geslo1 = request.forms.geslo1
    Geslo2 = request.forms.geslo2
    if request.forms.stanje:
        Stanje = request.forms.stanje
    else:
        Stanje = 0
    Ime = request.forms.ime
    Priimek = request.forms.priimek
    Rojstvo = request.forms.rojstvo
    Spol = request.forms.get("spol")
    #Slika = request.files.uploaded
    cur.execute("SELECT 1 FROM uporabnik WHERE uporabnisko_ime=%s", [UporabniskoIme])
    if cur.fetchone():
        # Uporabnik že obstaja
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('register.html', x=x, napaka = 'To uporabniško ime je že zavzeto', barva="red", uporabniki=cur)
    elif not Geslo1 == Geslo2:
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('register.html', x=x, napaka = 'Gesli se ne ujemata', barva="red", uporabniki=cur)
    #elif Slika is None:
    #    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
    #    return template('contacts.html', x=x, napaka = 'Niste dodali slike', uporabniki=cur)
    #elif Slika is not None:
        #name, ext = os.path.splitext(Slika.filename)
        #if ext.lower() not in ('.png','.jpg','.jpeg'):
        #    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        #    return template('contacts.html', x=x, napaka = 'Slika ni v pravem formatu', uporabniki=cur)
    elif UporabniskoIme and Geslo1 and Geslo2 and Ime and Priimek and Rojstvo and Spol: #zamaknjeno za tab, če vključimo slike
        #try:
            #print([str(UporabniskoIme), password_md5(Geslo1), int(Stanje), str(Ime), str(Priimek), str(Rojstvo), str(Spol)])
            #PraviRacun=int(RacunPython)
            cur.execute("INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika) VALUES (%s, %s, %s, %s, %s, to_date(%s, 'yyyy-mm-dd'), %s);", [str(UporabniskoIme), password_md5(Geslo1), int(Stanje), str(Ime), str(Priimek), str(Rojstvo), str(Spol)])
            #cur.execute("SELECT last_value FROM uporabnik_id_seq") #ID novega uporabnika
            #userid=cur.fetchone()
            #filename = str(userid[0]) + ext
            #Slika.filename = filename
            #save_path = os.path.join('static','images','uploads',filename)
            #Slika.save(save_path) # appends upload.filename automatically
            redirect('/register/')
            #cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
            #return template('register.html', x=0, napaka = "Vse OK", barva="red", uporabniki=cur)
        #except:
        #    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        #    return template('contacts.html', x=x, napaka = "Napaka pri dodajanju uporabnika", uporabniki=cur)
    else:
        cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        return template('register.html', x=x, napaka = 'Prosim izpolnite manjkajoče podatke', barva="red", uporabniki=cur)

@route("/user/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    cur.execute("SELECT * FROM uporabnik WHERE id = %s", [int(id)])
    Uporabnik = cur.fetchone()
    cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s", [int(id)])
    KupljenePesmi = cur.fetchall()
    cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s", [int(id)])
    KupljeniAlbumi = cur.fetchall()
    cur.execute("SELECT id,naslov FROM dogodek JOIN udelezba_dogodka ON dogodek.id = udelezba_dogodka.dogodekid WHERE uporabnikid = %s", [int(id)])
    UdelezeniDogodki = cur.fetchall()
    # Prikažemo predlogo
    return template("član.html", uporabnik=Uporabnik, pesmi=KupljenePesmi, albumi=KupljeniAlbumi, dogodki=UdelezeniDogodki)

@route("/song/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    if get_user():
        (username_login, ime_login, id_user) = get_user()
        cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s AND pesemid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
    else:
        username_login = None
        ze_kupljeno = False
    cur.execute("SELECT * FROM pesem WHERE id = %s", [int(id)])
    Pesem = cur.fetchone()
    (id, naslov, dolzina, izdan, zanr, cena) = Pesem
    cur.execute("SELECT naslov FROM zanr WHERE id = %s", [int(zanr)])
    Zanr = cur.fetchone()
    cur.execute("SELECT clan.ime FROM avtor_pesmi JOIN clan ON avtor_pesmi.clanid = clan.id WHERE pesemid = %s", [int(zanr)])
    Avtorji_p = []
    for (ime,) in cur:
        Avtorji_p.append(ime)
    cur.execute("SELECT clan.ime FROM avtor_besedila_pesmi JOIN clan ON avtor_besedila_pesmi.clanid = clan.id WHERE pesemid = %s", [int(zanr)])
    Avtorji_b = []
    for (ime,) in cur:
        Avtorji_b.append(ime)
    # Prikažemo predlogo
    cur.execute("SELECT album.id, album.naslov FROM album_pesem JOIN album ON album_pesem.albumid = album.id WHERE pesemid = %s", [int(id)])
    Albumi = cur.fetchall()
    return template("song.html", pesem=Pesem, zanr=Zanr, avtorji_pesmi = Avtorji_p, avtorji_besedila = Avtorji_b, albumi=Albumi, username=username_login, kupljeno = ze_kupljeno)

@post("/song/<id>/")
def user(id):
    if get_user():
        (username_login, ime_login, id_user) = get_user()
        cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s AND pesemid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
        if not ze_kupljeno:
            cur.execute("SELECT cena FROM pesem WHERE id = %s", [int(id)])
            (cena,)=cur.fetchone()
            cur.execute("UPDATE uporabnik SET stanje = stanje - %s WHERE id = %s", [int(cena), id_user])
            cur.execute("INSERT INTO kupil_pesem (pesemid, uporabnikid) VALUES (%s, %s)", [id, id_user])
            redirect('/song/'+str(id)+'/')

@route("/album/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    if get_user():
        (username_login, ime_login, id_user) = get_user()
        cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s AND albumid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
    else:
        username_login = None
        ze_kupljeno = False
    cur.execute("SELECT * FROM album WHERE id = %s", [int(id)])
    Album = cur.fetchone()
    cur.execute("SELECT SUM(dolzina) FROM album_pesem JOIN pesem ON album_pesem.pesemid = pesem.id WHERE albumid = %s", [int(id)])
    Dolzina = cur.fetchone()
    cur.execute("SELECT DISTINCT zanr.naslov FROM album_pesem JOIN pesem ON album_pesem.pesemid = pesem.id JOIN zanr ON pesem.zanr = zanr.id WHERE albumid = %s", [int(id)])
    Zanri = []
    for (naslov,) in cur:
        Zanri.append(naslov)
    cur.execute("SELECT pesem.id, pesem.naslov FROM album_pesem JOIN pesem ON album_pesem.pesemid = pesem.id WHERE albumid = %s", [int(id)])
    Pesmi = cur.fetchall()
    return template("album.html", album=Album, dolzina=Dolzina, zanri=Zanri, pesmi=Pesmi, username=username_login, kupljeno=ze_kupljeno)

@post("/album/<id>/")
def user(id):
    if get_user():
        (username_login, ime_login, id_user) = get_user()
        cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s AND albumid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
        if not ze_kupljeno:
            cur.execute("SELECT cena FROM album WHERE id = %s", [int(id)])
            (cena,)=cur.fetchone()
            cur.execute("UPDATE uporabnik SET stanje = stanje - %s WHERE id = %s", [int(cena), id_user])
            cur.execute("INSERT INTO kupil_album (albumid, uporabnikid) VALUES (%s, %s)", [id, id_user])
            redirect('/album/'+str(id)+'/')

@route("/dogodek/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    cur.execute("SELECT * FROM dogodek WHERE id = %s", [int(id)])
    Dogodek = cur.fetchone()
    cur.execute('SELECT pesem.id, pesem.naslov FROM izvedene_pesmi JOIN pesem ON izvedene_pesmi.pesemid = pesem.id WHERE dogodekid = 1', [int(id)])
    Pesmi = cur.fetchall()
    return template("dogodek.html", dogodek=Dogodek, pesmi=Pesmi)

@post("/user/<id>/")
def user(id):
    """Prikaži stran uporabnika"""
    # Ime uporabnika (hkrati preverimo, ali uporabnik sploh obstaja)
    sprememba = request.forms.stanje
    if sprememba:
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
# dodatne transakcije (novi kurzor)
cur1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na portu 8080, glej http://localhost:8080/
run(host='localhost', port=8080)
