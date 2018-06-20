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
        vrni njegov username, ime, id, stanje in podatek, če je admin. Če ni prijavljen,
       presumeri na stran za prijavo ali vrni None (advisno od auto_login).
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
            (username_login, ime_login, id_user) = r
            cur.execute("SELECT stanje FROM uporabnik WHERE id = %s", [int(id_user)])
            (stanje,) = cur.fetchone()
            r.append(stanje)
            cur.execute("SELECT admin FROM uporabnik WHERE id = %s", [int(id_user)])
            (admin,) = cur.fetchone()
            r.append(admin)
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/prijava/')
    else:
        return [None, None, 0, 0, None]

@route("/")
def main():
    """Preusmeri na index"""
    redirect("/index/")

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@get('/clani/')
def clani_stran():
    """Prikaze clane kolektiva"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    cur.execute("SELECT * FROM clan ORDER BY priimek, ime")
    return template('clani.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, clani=cur)

@get('/dogodki/')
def vsi_dogodki():
    """Prikaze dogodke, ki ustrezajo filtru"""
    query = dict(request.query)
    mnozica=''
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    #preverimo, če je uporabnik prijavljen in želi filtrirati po udelezenih dogodkih
    if username_login:
        if 'prikazi' not in query:
            query['prikazi'] = ''
        if query['prikazi'] == 'udelezeni':
            mnozica=''') INTERSECT (SELECT id,naslov,datum,tip FROM dogodek JOIN udelezba_dogodka ON udelezba_dogodka.dogodekid = dogodek.id WHERE uporabnikid = %s) '''
        elif query['prikazi'] == 'neudelezeni':
            mnozica=''') EXCEPT (SELECT id,naslov,datum,tip FROM dogodek JOIN udelezba_dogodka ON udelezba_dogodka.dogodekid = dogodek.id WHERE uporabnikid = %s) '''
    
    ORstring='''((SELECT * FROM dogodek WHERE 1=1\n'''
    parameters = [] #vektor parametrov za sql stavke
    #preverimo, kateri parametri niso izpolnjeni
    for parameter in ['search', 'spodnji', 'zgornji', 'urejanje', 'nacin_u', 'prikazi']:
        if parameter not in query:
            query[parameter] = ''
    
    if query['search'] != '': #iskanje po ključnih besedah
        ORstring += '''AND (LOWER(naslov) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    if query['spodnji'] != '':#filter za najmanjši datum
        ORstring += '''AND (datum >= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['spodnji']]
    if query['zgornji'] != '':#filter za največji datum
        ORstring += '''AND (datum <= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['zgornji']]

    if mnozica != '':
        ORstring += mnozica
        parameters = parameters + [id_user]
    else:
        ORstring += ''') '''

    if query['urejanje'] in ['naslov', 'datum']: #po čem urejamo
        ORstring += ''') ORDER BY ''' + query['urejanje']
    else:
        query['urejanje'] = 'datum' #če ni določeno, bomo uredili po datumu
        ORstring += ''') ORDER BY ''' + query['urejanje']
    
    if query['nacin_u'] in ['ASC', 'DESC']: #kako urejamo
        ORstring += ''' ''' + query['nacin_u']
    else:
        query['nacin_u'] = 'DESC' #če ni določeno, bomo uredili padajoče
        ORstring += ''' ''' + query['nacin_u']
    
    cur.execute(ORstring,parameters)
    Dogodki=cur.fetchall()
    return template('dogodki.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, username=username_login, dogodki=Dogodki, prikaz=query['prikazi'], iskanje=query['search'], sp_datum=query['spodnji'], zg_datum=query['zgornji'], ureditev=query['urejanje'], na_ureditve=query['nacin_u'], admin=admin)

@get('/litdela/')
def vsa_litdela():
    """Prikaze lit. dela, ki ustrezajo filtru"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    query = dict(request.query)
    ORstring='''
        SELECT * FROM lit_delo
        WHERE 1=1\n'''
    parameters = []

    #preverimo, kateri parametri niso izpolnjeni
    for parameter in ['search', 'spodnji', 'zgornji', 'urejanje', 'nacin_u']:
        if parameter not in query:
            query[parameter] = ''
    
    if query['search'] != '': #ključne besede
        ORstring += '''AND (LOWER(naslov) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    if query['spodnji'] != '': #najmanjši datum
        ORstring += '''AND (izdan >= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['spodnji']]
    if query['zgornji'] != '': #največji datum
        ORstring += '''AND (izdan <= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['zgornji']]
    if query['urejanje'] in ['naslov', 'izdan']:
        ORstring += '''ORDER BY ''' + query['urejanje']
    else:
        query['urejanje'] = 'izdan'
        ORstring += '''ORDER BY ''' + query['urejanje']
    if query['nacin_u'] in ['ASC', 'DESC']:
        ORstring += ''' ''' + query['nacin_u']
    else:
        query['nacin_u'] = 'DESC'
        ORstring += ''' ''' + query['nacin_u']
    cur.execute(ORstring,parameters)
    Litdela=cur.fetchall()
    return template('litdela.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, litdela=Litdela, iskanje=query['search'], sp_datum=query['spodnji'], zg_datum=query['zgornji'], ureditev=query['urejanje'], na_ureditve=query['nacin_u'], admin=admin)

@get('/albumi/')
def vsi_albumi():
    """Prikaze albume, ki ustrezajo filtru"""
    query = dict(request.query)
    mnozica=''
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    #preverimo, če je uporabnik prijavljen in želi filtrirati po kupljenih oz. ne-kupljenih albumih
    if username_login:
        if 'prikazi' not in query:
            query['prikazi'] = ''
        if query['prikazi'] == 'kupljene':
            mnozica=''') INTERSECT (SELECT id,naslov,izdan,opis,cena FROM album JOIN kupil_album ON kupil_album.albumid = album.id WHERE uporabnikid = %s) '''
        elif query['prikazi'] == 'nekupljene':
            mnozica=''') EXCEPT (SELECT id,naslov,izdan,opis,cena FROM album JOIN kupil_album ON kupil_album.albumid = album.id WHERE uporabnikid = %s) '''
    ORstring='''
        ((SELECT * FROM album
        WHERE 1=1\n'''
    parameters = []
    #preverimo, kateri parametri niso izpolnjeni
    for parameter in ['search', 'spodnji', 'zgornji', 'sp_cena', 'zg_cena', 'urejanje', 'nacin_u', 'prikazi']:
        if parameter not in query:
            query[parameter] = ''
    
    if query['search'] != '':
        ORstring += '''AND (LOWER(naslov) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    if query['spodnji'] != '':
        ORstring += '''AND (izdan >= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['spodnji']]
    if query['zgornji'] != '':
        ORstring += '''AND (izdan <= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['zgornji']]
    if query['sp_cena'] != '':
        ORstring += '''AND (cena >= %s )'''
        parameters = parameters + [query['sp_cena']]
    if query['zg_cena'] != '':
        ORstring += '''AND (cena <= %s )'''
        parameters = parameters + [query['zg_cena']]

    if mnozica != '':
        ORstring += mnozica
        parameters = parameters + [id_user]
    else:
        ORstring += ''') '''

    if query['urejanje'] in ['naslov', 'izdan', 'cena']:
        ORstring += ''') ORDER BY ''' + query['urejanje']
    else:
        query['urejanje'] = 'izdan'
        ORstring += ''') ORDER BY ''' + query['urejanje']
    if query['nacin_u'] in ['ASC', 'DESC']:
        ORstring += ''' ''' + query['nacin_u']
    else:
        query['nacin_u'] = 'DESC'
        ORstring += ''' ''' + query['nacin_u']
    cur.execute(ORstring,parameters)
    Albumi=cur.fetchall()
    return template('albumi.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, albumi=Albumi, prikaz=query['prikazi'], iskanje=query['search'], sp_datum=query['spodnji'], zg_datum=query['zgornji'], sp_cena = query['sp_cena'], zg_cena = query['zg_cena'], ureditev=query['urejanje'], na_ureditve=query['nacin_u'],admin=admin)

@get('/pesmi/')
def vse_pesmi():
    """Prikaze pesmi, ki ustrezajo filtru"""
    query = dict(request.query)
    mnozica=''
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        if 'prikazi' not in query:
            query['prikazi'] = ''
        if query['prikazi'] == 'kupljene':
            mnozica=''') INTERSECT (SELECT id,naslov,dolzina,izdan,zanr,cena FROM pesem JOIN kupil_pesem ON kupil_pesem.pesemid = pesem.id WHERE uporabnikid = %s) '''
        elif query['prikazi'] == 'nekupljene':
            mnozica=''') EXCEPT (SELECT id,naslov,dolzina,izdan,zanr,cena FROM pesem JOIN kupil_pesem ON kupil_pesem.pesemid = pesem.id WHERE uporabnikid = %s) '''
    ORstring='''
        ((SELECT * FROM pesem
        WHERE 1=1\n'''
    parameters = []

    for parameter in ['search', 'spodnji', 'zgornji', 'sp_cena', 'zg_cena', 'urejanje', 'nacin_u', 'prikazi']:
        if parameter not in query:
            query[parameter] = ''
    
    if query['search'] != '':
        ORstring += '''AND (LOWER(naslov) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    if query['spodnji'] != '':
        ORstring += '''AND (izdan >= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['spodnji']]
    if query['zgornji'] != '':
        ORstring += '''AND (izdan <= to_date(%s, 'yyyy-mm-dd') )'''
        parameters = parameters + [query['zgornji']]
    if query['sp_cena'] != '':
        ORstring += '''AND (cena >= %s )'''
        parameters = parameters + [query['sp_cena']]
    if query['zg_cena'] != '':
        ORstring += '''AND (cena <= %s )'''
        parameters = parameters + [query['zg_cena']]

    if mnozica != '':
        ORstring += mnozica
        parameters = parameters + [id_user]
    else:
        ORstring += ''') '''

    if query['urejanje'] in ['naslov', 'dolzina', 'izdan', 'cena']:
        ORstring += ''') ORDER BY ''' + query['urejanje']
    else:
        query['urejanje'] = 'izdan'
        ORstring += ''') ORDER BY ''' + query['urejanje']
    if query['nacin_u'] in ['ASC', 'DESC']:
        ORstring += ''' ''' + query['nacin_u']
    else:
        query['nacin_u'] = 'DESC'
        ORstring += ''' ''' + query['nacin_u']
    cur.execute(ORstring,parameters)
    Pesmi=cur.fetchall()
    return template('pesmi.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, pesmi=Pesmi, prikaz=query['prikazi'], iskanje=query['search'], sp_datum=query['spodnji'], zg_datum=query['zgornji'], sp_cena = query['sp_cena'], zg_cena = query['zg_cena'], ureditev=query['urejanje'], na_ureditve=query['nacin_u'], admin = admin)

@get('/galerija/')
def galerija_stran():
    """Prikaze galerijo s slikami"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    return template('galerija.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje)

@get('/index/')
def index_stran():
    """Prikaze prvo stran, kjer je predstavitev kolektiva"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT spol_uporabnika FROM uporabnik WHERE id = %s", [int(id_user)])
        (spol,) = cur.fetchone() #za sklanjatev
        cur.execute("SELECT dogodekid FROM udelezba_dogodka WHERE uporabnikid = %s", [int(id_user)])
        UdelezeniDogodki = cur.fetchall() #da bomo lahko označili že udeležene
    else:
        spol = None
        UdelezeniDogodki = None
    cur.execute("SELECT * FROM dogodek WHERE datum <= now()::date ORDER BY datum DESC, id DESC LIMIT 2")
    Dogodki1 = cur.fetchall() # dva pretekla dogodka
    cur.execute("SELECT * FROM dogodek WHERE datum > now()::date ORDER BY datum ASC, id DESC LIMIT 3")
    Dogodki2 = cur.fetchall() # trije prihajajoči dogodki
    
    return template('index.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, dogodki=Dogodki1, prihajajoci=Dogodki2, udelezeni=UdelezeniDogodki, spol=spol)

@get('/kontakt/')
def kontakt_stran():
    """Prikaze stran za kontakt"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    return template('kontakt.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje)

@get('/register/')
def registracija_stran():
    """Prikaze stran za registracijo"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        return template('register.html', napaka="Ste že prijavljeni!", barva="red", prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)
    else:
        return template('register.html', napaka="", barva="green", prijavljen_uporabnik=None, stanje=stanje, id_uporabnik=id_user)

@get('/prijava/')
def prijava_stran():
    """Prikaze stran za prijavo"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        return template('prijava.html', napaka="Ste že prijavljeni!", barva="red", prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)
    else:
        return template('prijava.html', napaka="", barva="green", prijavljen_uporabnik=None, stanje=stanje, id_uporabnik=id_user)

@get("/logout/")
def odjava():
    """Pobriši cookie in preusmeri na login."""
    response.delete_cookie('username', path='/', domain='localhost')
    redirect('/')

@post("/prijava/")
def prijava_uporabnika():
    """Obdela izpolnjeno formo za prijavo"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
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
                                   napaka="Uporabniško ime in geslo se ne ujemata. Pred prijavo se morate registrirati!", barva="red",
                                   username=username, prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)
        else:
            # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
            response.set_cookie('username', username, path='/', secret=secret)
            redirect("/")
    else:
        return template("prijava.html",
                                   napaka="Nepravilna prijava", barva="red",
                                   username=username, prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)

@get('/uporabniki/')
def vsi_uporabniki():
    """Prikaze vse registrirane uporabnike, ki zadoščajo filtru"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    query = dict(request.query)
    ORstring='''
        SELECT * FROM uporabnik
        WHERE 1=1\n'''
    parameters = []
    for parameter in ['search', 'nacin_u']:
        if parameter not in query:
            query[parameter] = ''
    
    if query['search'] != '':
        ORstring += '''AND (LOWER(uporabnisko_ime) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')
    ORstring += ''' ORDER BY uporabnisko_ime'''
    if query['nacin_u'] in ['ASC', 'DESC']:
        ORstring += ''' ''' + query['nacin_u']
    else:
        query['nacin_u'] = 'ASC'
        ORstring += ''' ''' + query['nacin_u']
    cur.execute(ORstring,parameters)
    return template('uporabniki.html', prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, napaka = "Vse OK", uporabniki=cur.fetchall(), iskanje=query['search'], na_ureditve=query['nacin_u'])

@post('/register/')
def registriraj_uporabnika():
    """Registrira novega uporabnika (ga doda v bazo)"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    UporabniskoIme = request.forms.uporabniskoime
    Geslo1 = request.forms.geslo1
    Geslo2 = request.forms.geslo2
    Stanje = 100
    Email = request.forms.kontakt
    Ime = request.forms.ime
    Priimek = request.forms.priimek
    Rojstvo = request.forms.rojstvo
    Spol = request.forms.get("spol")
    #Slika = request.files.uploaded
    cur.execute("SELECT 1 FROM uporabnik WHERE uporabnisko_ime=%s", [UporabniskoIme])
    if cur.fetchone():
        # Uporabnik že obstaja
        return template('register.html', napaka = 'To uporabniško ime je že zavzeto', barva="red", prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)
    elif not Geslo1 == Geslo2:
        return template('register.html', napaka = 'Gesli se ne ujemata', barva="red", prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)
    #elif Slika is None:
    #    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
    #    return template('contacts.html', x=x, napaka = 'Niste dodali slike', uporabniki=cur)
    #elif Slika is not None:
        #name, ext = os.path.splitext(Slika.filename)
        #if ext.lower() not in ('.png','.jpg','.jpeg'):
        #    cur.execute("SELECT * FROM uporabnik ORDER BY id, stanje")
        #    return template('contacts.html', x=x, napaka = 'Slika ni v pravem formatu', uporabniki=cur)
    elif UporabniskoIme and Geslo1 and Geslo2 and Ime and Priimek and Rojstvo and Spol: #zamaknjeno za tab, če vključimo slike
        cur.execute("INSERT INTO uporabnik(uporabnisko_ime, geslo, stanje, ime, priimek, rojstvo, spol_uporabnika, email) VALUES (%s, %s, %s, %s, %s, to_date(%s, 'yyyy-mm-dd'), %s, %s);", [str(UporabniskoIme), password_md5(Geslo1), int(Stanje), str(Ime), str(Priimek), str(Rojstvo), str(Spol), str(Email)])
        
        #cur.execute("SELECT last_value FROM uporabnik_id_seq") #ID novega uporabnika
        #userid=cur.fetchone()
        #filename = str(userid[0]) + ext
        #Slika.filename = filename
        #save_path = os.path.join('static','images','uploads',filename)
        #Slika.save(save_path) # appends upload.filename automatically
        
        redirect('/prijava/') #če se je uspešno registriral, ga preusmerimo na stran za prijavo.
    else:
        return template('register.html', napaka = 'Prosim izpolnite manjkajoče podatke', barva="red", prijavljen_uporabnik=username_login, stanje=stanje, id_uporabnik=id_user)

@route("/user/<id>/")
def uporabnik_stran(id):
    """Prikaži stran uporabnika"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    cur.execute("SELECT * FROM uporabnik WHERE id = %s", [int(id)])
    Uporabnik = cur.fetchone()
    cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s", [int(id)])
    KupljenePesmi = cur.fetchall()
    cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s", [int(id)])
    KupljeniAlbumi = cur.fetchall()
    cur.execute("SELECT id,naslov FROM dogodek JOIN udelezba_dogodka ON dogodek.id = udelezba_dogodka.dogodekid WHERE uporabnikid = %s", [int(id)])
    UdelezeniDogodki = cur.fetchall()
    return template("član.html", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, uporabnik=Uporabnik, pesmi=KupljenePesmi, albumi=KupljeniAlbumi, dogodki=UdelezeniDogodki)

@route("/song/<id>/")
def pesem_stran(id):
    """Prikaze stran pesmi"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s AND pesemid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
    else:
        ze_kupljeno = False
    cur.execute("SELECT * FROM pesem WHERE id = %s", [int(id)])
    Pesem = cur.fetchone()
    (id, naslov, dolzina, izdan, zanr, cena) = Pesem
    cur.execute("SELECT naslov FROM zanr WHERE id = %s", [int(zanr)])
    Zanr = cur.fetchone()
    cur.execute("SELECT clan.ime FROM avtor_pesmi JOIN clan ON avtor_pesmi.clanid = clan.id WHERE pesemid = %s", [int(id)])
    Avtorji_p = []
    for (ime,) in cur:
        Avtorji_p.append(ime)
    cur.execute("SELECT clan.ime FROM avtor_besedila_pesmi JOIN clan ON avtor_besedila_pesmi.clanid = clan.id WHERE pesemid = %s", [int(id)])
    Avtorji_b = []
    for (ime,) in cur:
        Avtorji_b.append(ime)
    cur.execute("SELECT album.id, album.naslov FROM album_pesem JOIN album ON album_pesem.albumid = album.id WHERE pesemid = %s", [int(id)])
    Albumi = cur.fetchall()
    cur.execute("SELECT dogodek.id, dogodek.naslov FROM izvedene_pesmi JOIN dogodek ON izvedene_pesmi.dogodekid = dogodek.id WHERE pesemid = %s", [int(id)])
    Dogodki = cur.fetchall()
    return template("song.html", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, pesem=Pesem, zanr=Zanr, avtorji_pesmi = Avtorji_p, avtorji_besedila = Avtorji_b, albumi=Albumi, dogodki=Dogodki, username=username_login, kupljeno = ze_kupljeno)

@route("/litdelo/<id>/")
def litdelo_stran(id):
    """Prikaze stran lit. dela"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    cur.execute("SELECT * FROM lit_delo WHERE id = %s", [int(id)])
    Litdelo = cur.fetchone()
    (id, naslov, izdan, zaloznik, tip) = Litdelo
    cur.execute("SELECT naslov FROM tip_lit_dela WHERE id = %s", [int(tip)])
    Tip = cur.fetchone()
    cur.execute("SELECT clan.ime FROM avtor_lit_dela JOIN clan ON avtor_lit_dela.clanid = clan.id WHERE litdeloid = %s", [int(id)])
    Avtorji_l = []
    for (ime,) in cur:
        Avtorji_l.append(ime)
    cur.execute("SELECT dogodek.id, dogodek.naslov FROM izvedena_lit_dela JOIN dogodek ON izvedena_lit_dela.dogodekid = dogodek.id WHERE litdeloid = %s", [int(id)])
    Dogodki = cur.fetchall()
    return template("litdelo.html", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, litdelo=Litdelo, tip=Tip, avtorji_litdela = Avtorji_l, dogodki=Dogodki)

@post("/song/<id>/")
def kupi_pesem(id):
    """Uporabnik kupi pesem"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s AND pesemid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
        cur.execute("SELECT cena FROM pesem WHERE id = %s", [int(id)])
        (cena,)=cur.fetchone()
        if not ze_kupljeno and stanje >= cena: #če je stanje uporabnika večje od cene in te pesmi še nismo kupili, potem jo lahko.
            cur.execute("UPDATE uporabnik SET stanje = stanje - %s WHERE id = %s", [int(cena), id_user])
            cur.execute("INSERT INTO kupil_pesem (pesemid, uporabnikid) VALUES (%s, %s)", [id, id_user])
    redirect('/song/'+str(id)+'/')

@route("/album/<id>/")
def album_stran(id):
    """Prikaze stran albuma"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s AND albumid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
    else:
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
    return template("album.html", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, album=Album, dolzina=Dolzina, zanri=Zanri, pesmi=Pesmi, username=username_login, kupljeno=ze_kupljeno)

@post("/album/<id>/")
def kupi_album(id):
    """Uporabnik kupi album"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM album JOIN kupil_album ON album.id = kupil_album.albumid WHERE uporabnikid = %s AND albumid = %s", [int(id_user), int(id)])
        ze_kupljeno = cur.fetchone()
        cur.execute("SELECT cena FROM album WHERE id = %s", [int(id)])
        (cena,)=cur.fetchone()
        if not ze_kupljeno and stanje >= cena:
            cur.execute("UPDATE uporabnik SET stanje = stanje - %s WHERE id = %s", [int(cena), id_user])
            cur.execute("INSERT INTO kupil_album (albumid, uporabnikid) VALUES (%s, %s)", [id, id_user])
            cur.execute("SELECT pesem.id FROM album_pesem JOIN pesem ON album_pesem.pesemid = pesem.id WHERE albumid = %s", [int(id)])
            pesmi = cur.fetchall()
            for (pesem_id,) in pesmi: #če smo kupili album, smo kupili tudi vse pesmi
                cur.execute("SELECT id,naslov FROM pesem JOIN kupil_pesem ON pesem.id = kupil_pesem.pesemid WHERE uporabnikid = %s AND pesemid = %s", [int(id_user), int(pesem_id)])
                ze_kupljeno = cur.fetchone()
                if not ze_kupljeno:
                    cur.execute("INSERT INTO kupil_pesem (pesemid, uporabnikid) VALUES (%s, %s)", [int(pesem_id), id_user])
    redirect('/album/'+str(id)+'/')

@route("/dogodek/<id>/")
def dogodek_stran(id):
    """Prikaze stran dogodka"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM dogodek JOIN udelezba_dogodka ON dogodek.id = udelezba_dogodka.dogodekid WHERE uporabnikid = %s AND dogodekid = %s", [int(id_user), int(id)])
        udelezeno = cur.fetchone()
    else:
        udelezeno = False
    cur.execute("SELECT * FROM dogodek WHERE id = %s", [int(id)])
    Dogodek = cur.fetchone()
    cur.execute('SELECT pesem.id, pesem.naslov FROM izvedene_pesmi JOIN pesem ON izvedene_pesmi.pesemid = pesem.id WHERE dogodekid = %s', [int(id)])
    Pesmi = cur.fetchall()
    cur.execute('SELECT lit_delo.id, lit_delo.naslov FROM izvedena_lit_dela JOIN lit_delo ON izvedena_lit_dela.litdeloid = lit_delo.id WHERE dogodekid = %s', [int(id)])
    Litdela = cur.fetchall()
    return template("dogodek.html", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, dogodek=Dogodek, pesmi=Pesmi, litdela=Litdela, username = username_login, udelezeno=udelezeno)

@post("/dogodek/<id>/")
def udelezi_dogodek(id):
    """Uporabnik potrdi udelezbo na dogodku"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        cur.execute("SELECT id,naslov FROM dogodek JOIN udelezba_dogodka ON dogodek.id = udelezba_dogodka.dogodekid WHERE uporabnikid = %s AND dogodekid = %s", [int(id_user), int(id)])
        udelezeno = cur.fetchone()
        if not udelezeno:
            cur.execute("INSERT INTO udelezba_dogodka (dogodekid, uporabnikid) VALUES (%s, %s)", [id, id_user])
            redirect('/dogodek/'+str(id)+'/')

@post("/user/<id>/")
def ponaredi_stanje(id):
    """Uporabnik ponaredi drugemu uporabniku stanje"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login:
        sprememba = request.forms.stanje
        if sprememba and int(sprememba) > 0:
            cur.execute("UPDATE uporabnik SET stanje = stanje + %s WHERE id = %s", [sprememba, int(id)])
    redirect('/user/'+str(id)+'/')

@get('/add_pesem/')
def dodaj_pesem_stran():
    """Admin lahko doda novo pesem"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        cur.execute("SELECT id, naslov FROM zanr", [int(id_user)])
        zanri = cur.fetchall()
        cur.execute("SELECT id, ime FROM clan", [int(id_user)])
        clani = cur.fetchall()
        return template('add_pesem.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, zanri = zanri, clani=clani)
    else:
        return template('add_pesem.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje=stanje, admin=admin, zanri = [], clani=[])

@post('/add_pesem/')
def dodaj_pesem():
    """Admin lahko doda novo pesem"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.naslov
            Dolzina = request.forms.dolzina
            Izdana = request.forms.izdan
            Zanr = request.forms.get("zanr")
            Cena = request.forms.cena
            Minute = int(Dolzina)//60
            Sekunde = int(Dolzina)%60
            AvtorP = request.forms.getall('avtorp')
            AvtorB = request.forms.getall('avtorb')
            if Naslov and Dolzina and Izdana and Zanr and Cena and AvtorP and AvtorB:
                cur.execute("INSERT INTO pesem(naslov, dolzina, izdan, zanr, cena) VALUES (%s, '%s minutes %s seconds', to_date(%s, 'yyyy-mm-dd'), %s, %s);", [str(Naslov), int(Minute), int(Sekunde), str(Izdana), int(Zanr), int(Cena)])
                cur.execute("SELECT last_value FROM pesem_id_seq") #ID nove pesmi
                (id_pesem,) = cur.fetchone()
                for avtor in AvtorP:
                    cur.execute("INSERT INTO avtor_pesmi(pesemid, clanid) VALUES (%s, %s);", [int(id_pesem), int(avtor)])
                for avtor in AvtorB:
                    cur.execute("INSERT INTO avtor_besedila_pesmi(pesemid, clanid) VALUES (%s, %s);", [int(id_pesem), int(avtor)])
    redirect('/add_pesem/')

@get('/add_zanr/')
def dodaj_zanr_stran():
    """Admin lahko doda nov zanr pesmi"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        return template('add_zanr.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin)
    else:
        return template('add_zanr.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin)

@post('/add_zanr/')
def dodaj_zanr():
    """Admin lahko doda nov zanr pesmi"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.naslov
            if Naslov:
                cur.execute("INSERT INTO zanr(naslov) VALUES (%s);", [str(Naslov)])
    redirect('/add_zanr/')

@get('/add_album/')
def dodaj_album_stran():
    """Admin lahko doda nov album"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        cur.execute("SELECT id, naslov FROM pesem", [int(id_user)])
        pesmi = cur.fetchall()
        return template('add_album.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, pesmi = pesmi)
    else:
        return template('add_album.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, pesmi = [])

@post('/add_album/')
def dodaj_album():
    """Admin lahko doda nov album"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.naslov
            Izdan = request.forms.izdan
            Opis = request.forms.get("opis")
            Cena = request.forms.cena
            VsebujeP = request.forms.getall('vsebujep')
            if Naslov and Izdan and Opis and Cena and VsebujeP:
                cur.execute("INSERT INTO album(naslov, izdan, opis, cena) VALUES (%s, to_date(%s, 'yyyy-mm-dd'), %s, %s);", [str(Naslov), str(Izdan), str(Opis), int(Cena)])
                cur.execute("SELECT last_value FROM album_id_seq") #ID nove pesmi
                (id_album,) = cur.fetchone()
                for pesem in VsebujeP:
                    cur.execute("INSERT INTO album_pesem(pesemid, albumid) VALUES (%s, %s);", [int(pesem), int(id_album)])
    redirect('/add_album/')

@get('/add_litdelo/')
def dodaj_litdelo_stran():
    """Admin lahko doda novo lit. delo"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        cur.execute("SELECT id, naslov FROM tip_lit_dela", [int(id_user)])
        tipi = cur.fetchall()
        cur.execute("SELECT id, ime FROM clan", [int(id_user)])
        clani = cur.fetchall()
        return template('add_litdelo.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, tipi = tipi, clani=clani)
    else:
        return template('add_litdelo.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, tipi = [], clani=[])

@post('/add_litdelo/')
def dodaj_litdelo():
    """Admin lahko doda novo lit. delo"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.get("naslov")
            Izdan = request.forms.izdan
            Zaloznik = request.forms.zaloznik
            Tip = request.forms.get("tip")
            AvtorL = request.forms.getall('avtorl')
            if Naslov and Izdan and Zaloznik and Tip and AvtorL:
                cur.execute("INSERT INTO lit_delo(naslov, izdan, zaloznik, tip) VALUES (%s, to_date(%s, 'yyyy-mm-dd'), %s, %s);", [str(Naslov), str(Izdan), str(Zaloznik), int(Tip)])
                cur.execute("SELECT last_value FROM lit_delo_id_seq") #ID nove pesmi
                (id_litdelo,) = cur.fetchone()
                for avtor in AvtorL:
                    cur.execute("INSERT INTO avtor_lit_dela(litdeloid, clanid) VALUES (%s, %s);", [int(id_litdelo), int(avtor)])
    redirect('/add_litdelo/')

@get('/add_tip/')
def dodaj_tip_stran():
    """Admin lahko doda nov tip lit. dela"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        return template('add_tip.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin)
    else:
        return template('add_tip.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin)

@post('/add_tip/')
def dodaj_tip():
    """Admin lahko doda nov tip lit. dela"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.naslov
            if Naslov:
                cur.execute("INSERT INTO tip_lit_dela(naslov) VALUES (%s);", [str(Naslov)])
    redirect('/add_tip/')

@get('/add_dogodek/')
def dodaj_dogodek_stran():
    """Admin lahko doda nov dogodek"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
        cur.execute("SELECT id, naslov FROM pesem", [int(id_user)])
        pesmi = cur.fetchall()
        cur.execute("SELECT id, naslov FROM lit_delo", [int(id_user)])
        litdela = cur.fetchall()
        return template('add_dogodek.html', napaka="", barva="green", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, pesmi = pesmi, litdela=litdela)
    else:
        return template('add_dogodek.html', napaka="Niste admin.", barva="red", prijavljen_uporabnik=username_login, id_uporabnik=id_user, stanje = stanje, admin=admin, pesmi = [], litdela=[])

@post('/add_dogodek/')
def dodaj_dogodek():
    """Admin lahko doda nov dogodek"""
    (username_login, ime_login, id_user, stanje, admin) = get_user()
    if username_login and admin:
            Naslov = request.forms.naslov
            Datum = request.forms.datum
            Tip = request.forms.get("tip")
            IzvedeneP = request.forms.getall('izvedenep')
            IzvedeneL = request.forms.getall('izvedenel')
            if Naslov and Datum and Tip:
                cur.execute("INSERT INTO dogodek(naslov, datum, tip) VALUES (%s, to_date(%s, 'yyyy-mm-dd'), %s);", [str(Naslov), str(Datum), str(Tip)])
                cur.execute("SELECT last_value FROM dogodek_id_seq") #ID novega dogodka
                (id_dogodka,) = cur.fetchone()
                for id_pesmi in IzvedeneP:
                    cur.execute("INSERT INTO izvedene_pesmi(dogodekid, pesemid) VALUES (%s, %s);", [int(id_dogodka), int(id_pesmi)])
                for id_lit_dela in IzvedeneL:
                    cur.execute("INSERT INTO izvedena_lit_dela(dogodekid, litdeloid) VALUES (%s, %s);", [int(id_dogodka), int(id_lit_dela)])
    redirect('/add_dogodek/')

######################################################################
# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na portu 8080, glej http://localhost:8080/
run(host='localhost', port=8080)
