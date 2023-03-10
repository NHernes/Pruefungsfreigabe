import datetime
import json,requests
import datetime
from dateutil.relativedelta import *
from dateutil.easter import *
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
import eel
import numpy as np
from threading import Thread
import csv
import config


eel.init("web")

def oauth():
    global access_token

    client_id=config.client_id
    client_secret=config.client_secret
    auth_url=config.auth_url
    code_url=config.code_url
    code=config.code
    refresh_token=config.refresh_token
    
    client_id=client_id
    client_secret=client_secret
    auth_url=auth_url
    code_url=code_url
    code=code
    url="https://webexapis.com/v1/authorize"

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    """
    r= requests.post(url=code_url,headers=headers)
    print(r.text)
    """
    """
    with open("access_token_webex.txt","r") as f:
        access_token=f.read()
    
    with open("refresh_token_webex.txt","r") as g:
        refresh_token=g.read()


    url="https://webexapis.com/v1/people/me"

    headers={
        "Authorization": f"Bearer {access_token}",
        "content-type": "application/x-www-form-urlencoded; charset=utf-8;"
    }
    
    r = requests.get(url,headers=headers)
    if r.status_code==200:
        pass
    
    else:
    """
    url=f"https://webexapis.com/v1/access_token?grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}"

    r = requests.post(url,headers=headers)
    r=json.loads(r.text)
    r=r["access_token"]

    """
    with open("access_token_webex.txt","w") as f:
        f.write(r)
    """

    access_token=r

    return access_token

def oauth_lplus(name,pw):
    lplus_client_id= config.lplus_client_id
    lplus_client_secret= config.lplus_client_secret

    benutzername=name
    passwort=pw

    payload = {
        'grant_type': 'password',
        'client_id': lplus_client_id,
        'client_secret': lplus_client_secret,
        'username': benutzername,
        'password': passwort}
    r = requests.post('https://fub.lplus-teststudio.de/token', data=payload)

    if r.status_code!=200:
        return bool(0)
    else:
        token=json.loads(r.text)['access_token']
        return token

@eel.expose
def meeting_informationen_abrufen():
    global liste1
    access_token=oauth()
    heute_datum=datetime.now().date()
    beginn=datetime(heute_datum.year, heute_datum.month, heute_datum.day, 0, 0, 0).isoformat()
    ende=datetime(heute_datum.year, heute_datum.month, heute_datum.day, 21, 0, 0).isoformat()

    url=f"https://webexapis.com/v1/meetings?meetingType=scheduledMeeting&scheduledType=meeting&from={str(beginn)}&to={str(ende)}"
                                                        
    headers={
        "Authorization": f"Bearer {access_token}"
    }
        
    r = requests.get(url, headers=headers)
    daten=json.loads(r.text)
    daten=daten["items"]

    heute=datetime.now().strftime("%Y-%m-%d")

    liste1=[]
    liste2=[]
    for count,i in enumerate(daten):
        
        if heute in daten[count]["start"]:
            liste1=liste1+[[daten[count]["id"],daten[count]["start"],daten[count]["title"]]]
            liste2.append(daten[count]["title"])

    return liste2


@eel.expose
def tn_abrufen(meeting_auswahl):
    global liste1,personen_webex_meeting
    access_token=oauth()
    
    for count,i in enumerate(liste1):
        if meeting_auswahl == liste1[count][2]:
            pr??fungs_id=liste1[count][0]
    url=f"https://webexapis.com/v1/meetingParticipants?meetingId={pr??fungs_id}&max=100"
                                                      
    headers={
        "Authorization": f"Bearer {access_token}"
    }

    r = requests.get(url, headers=headers)
    daten_tn=json.loads(r.text)
    daten_tn=daten_tn["items"]

    head=r.headers
    while "link" in head.keys():
        url=head["link"]
        url=url[1:]

        while ">" in url:
            url=url[:-1]
                                                        
        headers={
            "Authorization": f"Bearer {access_token}"
        }

        r = requests.get(url, headers=headers)

        daten_erweiterte_abfrage=(json.loads(r.text))["items"][0]
        daten_tn.append(daten_erweiterte_abfrage)

        head=r.headers


    personen_webex_meeting=[]

    for count,eintr??ge in enumerate(daten_tn):

        zedatname=daten_tn[count]["email"]
        
        while "@" in zedatname:
            zedatname=zedatname[:-1]
        if zedatname!="eexamwebex" and daten_tn[count]["state"]=="joined":
            personen_webex_meeting=personen_webex_meeting+[[daten_tn[count]["displayName"],zedatname,"???"]]


    return personen_webex_meeting


@eel.expose
def lplus_lizenzen_abrufen(name,pw):
    global lizenzdaten,token,lplus_client_id,lplus_client_secret, benutzername, passwort

    benutzername=name
    passwort=pw
    
    auth_lplus=oauth_lplus(benutzername,passwort)

    if not auth_lplus:
        return auth_lplus

    else:
        token=auth_lplus

        headers={
            "Authorization": f"Bearer {token}"
            }

        r = requests.get("https://fub.lplus-teststudio.de/publicapi/v1/licences", 
            headers=headers)


        lizenzen=json.loads(r.text)
        lizenznamen=[]
        lizenzdaten={}
        
        def auswahl_g??ltigkeitszeitraum(lizenznamen,lizenzdaten): #Hier werden die Lizenzen nach G??ltigkeitszeitraum gefiltert
            z??hler=-1
            for eintrag in lizenzen:
                z??hler+=1
                if (lizenzen[z??hler]["licenceTimeLimits"]!=[]):
                    #print(json.dumps(i, sort_keys=True, indent=4, separators=(",", ": ")))
                    
                    
                    zeitr??ume=lizenzen[z??hler]["licenceTimeLimits"]
                    if type(zeitr??ume)==list:
                        counter=-1
                        for timeslots in zeitr??ume:
                            counter+=1
                            uhrzeit_lizenz=lizenzen[z??hler]["licenceTimeLimits"][counter]["from"][11:16]
                            uhrzeit_lizenz=datetime.strptime(uhrzeit_lizenz,"%H:%M")+timedelta(hours=2)
                            uhrzeit_lizenz=uhrzeit_lizenz.time()
                            lizenzen[z??hler]["licenceTimeLimits"][counter]["from"]=(isoparse(lizenzen[z??hler]["licenceTimeLimits"][counter]["from"])+timedelta(hours=2)).date()
                            heute=datetime.now().date()
                            if lizenzen[z??hler]["licenceTimeLimits"][counter]["from"]==heute:
                                lizenznamen=lizenznamen+[f'{lizenzen[z??hler]["name"]}|{lizenzen[z??hler]["id"]}']
                                lizenzdaten.update({lizenzen[z??hler]["name"]:lizenzen[z??hler]["id"]})
                    
                    else:
                        uhrzeit_lizenz=lizenzen[z??hler]["licenceTimeLimits"][counter]["from"][11:16]
                        uhrzeit_lizenz=datetime.strptime(uhrzeit_lizenz,"%H:%M")+timedelta(hours=2)
                        uhrzeit_lizenz=uhrzeit_lizenz.time()
                        lizenzen[z??hler]["licenceTimeLimits"][0]["from"]=(isoparse(lizenzen[z??hler]["licenceTimeLimits"][0]["from"])+timedelta(hours=2)).date()
                        heute=datetime.now().date()
                        if lizenzen[z??hler]["licenceTimeLimits"][0]["from"]==heute:
                            lizenznamen=lizenznamen+[f'{lizenzen[z??hler]["name"]}|{lizenzen[z??hler]["id"]}']
                            lizenzdaten.update({lizenzen[z??hler]["name"]:lizenzen[z??hler]["id"]})

            return lizenznamen

        def auswahl_alle_lizenzen(lizenznamen,lizenzdaten):
            for count,eintrag in enumerate(lizenzen):
                lizenznamen=lizenznamen+[f'{lizenzen[count]["name"]} | {lizenzen[count]["id"]}']
                
                lizenzdaten.update({lizenzen[count]["name"]:lizenzen[count]["id"]})
            return lizenznamen

        lizenznamen=auswahl_alle_lizenzen(lizenznamen,lizenzdaten)

        if lizenznamen==[]:
            lizenznamen="Keine Lizenzen"


        return lizenznamen

@eel.expose
def lplus_f??cher_abrufen(fach):
    global liste_f??cher_vollst??ndig

    liste_f??cher=[]
    liste_f??cher_vollst??ndig={}

    for key,item in lizenzdaten.items():

        if key in fach:
            lizenz_id=item

            token=oauth_lplus(benutzername,passwort)
            headers={
            "Authorization": f"Bearer {token}"
            }
            r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/licences/{lizenz_id}/subjects", 
                headers=headers)
            alle_f??cher=json.loads(r.text)
            for eintrag in alle_f??cher:
                liste_f??cher=liste_f??cher+[f'{eintrag["name"]} |{eintrag["id"]}']
                liste_f??cher_vollst??ndig.update({eintrag["name"]:eintrag["id"]})

    
    return liste_f??cher
    
@eel.expose
def pr??fung_freigeben(lizenz_id,f??cher_id_array):
    global freigabez??hler,excel_download_liste

    while "|" in lizenz_id:
        lizenz_id=lizenz_id[1:]


    for count,eintrag in enumerate(f??cher_id_array):
        while "|" in f??cher_id_array[count]:
            f??cher_id_array[count]=f??cher_id_array[count][1:]
    
    token=oauth_lplus(benutzername,passwort)
    headers={
    "Authorization": f"Bearer {token}"
    }
    r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/licences/{lizenz_id}/candidateRelations", 
    headers=headers)

    daten_gemeldete_nutzer=json.loads(r.text)

    if len(daten_gemeldete_nutzer)<10:
        for eintrag in daten_gemeldete_nutzer:
            tn_id=eintrag["userDetailId"]
            r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{tn_id}", 
            headers=headers)

            if r.status_code==200:
                eel.progress_abgerufene_personen(1)

            tn_name=json.loads(r.text)

            matrikelnummer=tn_name["importKey"]
            eintrag.update({"matrikelnummer":matrikelnummer})
                
            if not isinstance(tn_name["firstName"], str):
                tn_name["firstName"]=""
            if not isinstance(tn_name["lastName"], str):
                tn_name["lastName"]=""
            tn_klarname=f'{tn_name["firstName"]} {tn_name["lastName"]}'
            tn_name=tn_name["userName"]

            eintrag.update({"tn_name":tn_name})
            eintrag.update({"klarname":tn_klarname})


    if len(daten_gemeldete_nutzer)>=10:
        pieces = 10
        new_arrays = np.array_split(daten_gemeldete_nutzer, pieces)


        master_liste_gemeldete_nutzer=[]

        def nutzernamen_ziehen(array):
            daten_gemeldete_nutzer1=array

            token=oauth_lplus(benutzername,passwort)
            headers={
            "Authorization": f"Bearer {token}"
            }

            for eintrag in daten_gemeldete_nutzer1:
                tn_id=eintrag["userDetailId"]
                r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{tn_id}", 
                headers=headers)

                if r.status_code==200:
                    eel.progress_abgerufene_personen(1)

                tn_name=json.loads(r.text)

                matrikelnummer=tn_name["importKey"]
                eintrag.update({"matrikelnummer":matrikelnummer})
                
                if not isinstance(tn_name["firstName"], str):
                    tn_name["firstName"]=""
                if not isinstance(tn_name["lastName"], str):
                    tn_name["lastName"]=""
                tn_klarname=tn_name["firstName"]+" "+tn_name["lastName"]
                tn_name=tn_name["userName"]

                eintrag.update({"tn_name":tn_name})
                eintrag.update({"klarname":tn_klarname})
                master_liste_gemeldete_nutzer.append(eintrag)

        threads = []
        for i in range(0,10):
            threads.append(Thread(target=nutzernamen_ziehen, args=(new_arrays[i],)))
            threads[-1].start()
        for thread in threads:
            thread.join()
        
        daten_gemeldete_nutzer=master_liste_gemeldete_nutzer


    
    headers2={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    freigabez??hler=0
    if len(personen_webex_meeting)<10:
        for eintrag1 in personen_webex_meeting:
            for eintrag2 in daten_gemeldete_nutzer:
                if eintrag1[0] == eintrag2["klarname"]:
      
                    for eintrag3 in f??cher_id_array:            
                        payload={

                            "LicenceId":eintrag2["licenceId"],
                            "ExaminationpartId":eintrag3,
                            "IsReleased":bool(1)

                        }
                        payload=json.dumps(payload)
                        url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidates/{eintrag2['userDetailId']}/releases/"
                        r = requests.post(url, headers=headers2, data=payload)

                        json_data = json.loads(r.text)

                        if r.status_code==200:
                            eintrag1[2]="??????"
                            freigabez??hler+=1
                            eintrag1.append(eintrag2["matrikelnummer"])
                            eel.progress_freigegebene_pr??fungen(1)
                            
                        else:
                            pass
                 
    if len(personen_webex_meeting)>=10:

        pieces = 10
        new_arrays = np.array_split(personen_webex_meeting, pieces)

        token=oauth_lplus(benutzername,passwort)
        headers={
        "Authorization": f"Bearer {token}"
        }

        def freigabe_thread(array):
            global freigabez??hler
            for eintrag1 in array:
                for eintrag2 in daten_gemeldete_nutzer:
                    if eintrag1[0] == eintrag2["klarname"]:
                    
                        for eintrag3 in f??cher_id_array:            
                            payload={

                                "LicenceId":eintrag2["licenceId"],
                                "ExaminationpartId":eintrag3,
                                "IsReleased":bool(1)

                            }
                            payload=json.dumps(payload)
                            url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{eintrag2['userDetailId']}/releases/"
                            r = requests.post(url, headers=headers2, data=payload)

                            json_data = json.loads(r.text)
                    
                            if r.status_code==200:
                                freigabez??hler+=1
                                eel.freigegebene_pr??fungen_anzahl(1)
                                for eintrag in personen_webex_meeting:
                                    if eintrag2["klarname"] in eintrag[0]:
                                        eintrag.append(eintrag2["matrikelnummer"])
                                        eintrag[2]="??????"

                            else:
                                pass
 
        threads = []
        for i in range(0,10):
            threads.append(Thread(target=freigabe_thread, args=(new_arrays[i],)))
            threads[-1].start()
        for thread in threads:
            thread.join()
        
    personen_webex_meeting.sort()
    excel_download_liste=personen_webex_meeting

    excel_download_liste=daten_gemeldete_nutzer
    
    if personen_webex_meeting!=[]:
        for eintrag in excel_download_liste:
            for i in personen_webex_meeting:
                print( eintrag["klarname"],i[0])
                if eintrag["klarname"] == i[0]: 
                    eintrag["Webex anwesend"]="Ja"
                    print("hier")
                    eintrag["Pr??fung freigegeben"]="Ja"

                else:
                    eintrag["Webex anwesend"]="Nein"
                    eintrag["Pr??fung freigegeben"]="Nein"
    else:
        for eintrag in excel_download_liste:
            eintrag["Webex anwesend"]="Nein"
    print(excel_download_liste)

    return personen_webex_meeting,freigabez??hler
            

@eel.expose
def ??bersicht_anzahl_kandidaten(lizenz_id_??bersicht,f??cher_id_array_??bersicht):
    lizenz_id=lizenz_id_??bersicht
    f??cher_id_array=f??cher_id_array_??bersicht
    while "|" in lizenz_id:
        lizenz_id=lizenz_id[1:]

    z??hler=-1
    for eintrag in f??cher_id_array:
        z??hler+=1
        while "|" in f??cher_id_array[z??hler]:
            f??cher_id_array[z??hler]=f??cher_id_array[z??hler][1:]
    
    token=oauth_lplus(benutzername,passwort)
    headers={
    "Authorization": f"Bearer {token}"
    }
    r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/licences/{lizenz_id}/candidateRelations", 
    headers=headers)

    daten_gemeldete_nutzer=json.loads(r.text)
    anzahl_pr??flinge=0
    anzahl_f??cher_freigaben=0

    for eintrag in daten_gemeldete_nutzer:
        anzahl_pr??flinge+=1

        for fach in eintrag["examinationPartIds"]:
            if str(fach) in f??cher_id_array:
                anzahl_f??cher_freigaben+=1

    return [anzahl_pr??flinge,anzahl_f??cher_freigaben]

@eel.expose
def alle_pr??fungen_freigeben(lizenz_id,f??cher_id_array):
    global freigabez??hler,personen_webex_meeting,excel_download_liste

    if 'personen_webex_meeting' not in globals():
        personen_webex_meeting=[]

    while "|" in lizenz_id:
        lizenz_id=lizenz_id[1:]

    z??hler=-1
    for eintrag in f??cher_id_array:
        z??hler+=1
        while "|" in f??cher_id_array[z??hler]:
            f??cher_id_array[z??hler]=f??cher_id_array[z??hler][1:]
    
    token=oauth_lplus(benutzername,passwort)
    headers={
    "Authorization": f"Bearer {token}"
    }
    r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/licences/{lizenz_id}/candidateRelations", 
    headers=headers)

    daten_gemeldete_nutzer=json.loads(r.text)

    if len(daten_gemeldete_nutzer)<10:
        for eintrag in daten_gemeldete_nutzer:
            tn_id=eintrag["userDetailId"]
            r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{tn_id}", 
            headers=headers)
            
            if r.status_code==200:
                eel.progress_abgerufene_personen(1)

            tn_name=json.loads(r.text)

            matrikelnummer=tn_name["importKey"]
            eintrag.update({"matrikelnummer":matrikelnummer})

            if not isinstance(tn_name["firstName"], str):
                tn_name["firstName"]=""
            if not isinstance(tn_name["lastName"], str):
                tn_name["lastName"]=""
            tn_klarname=tn_name["firstName"]+" "+tn_name["lastName"]
            tn_name=tn_name["userName"]
 
            eintrag.update({"tn_name":tn_name})
            eintrag.update({"klarname":tn_klarname})

    
    if len(daten_gemeldete_nutzer)>=10:
        pieces = 10
        new_arrays = np.array_split(daten_gemeldete_nutzer, pieces)


        master_liste_gemeldete_nutzer=[]

        def nutzernamen_ziehen(array):
            daten_gemeldete_nutzer1=array
            for eintrag in daten_gemeldete_nutzer1:

                tn_id=eintrag["userDetailId"]
                r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{tn_id}", 
                headers=headers)

                if r.status_code==200:
                    eel.progress_abgerufene_personen(1)

                tn_name=json.loads(r.text)

                matrikelnummer=tn_name["importKey"]
                eintrag.update({"matrikelnummer":matrikelnummer})

                if not isinstance(tn_name["firstName"], str):
                    tn_name["firstName"]=""
                if not isinstance(tn_name["lastName"], str):
                    tn_name["lastName"]=""
                tn_klarname=tn_name["firstName"]+" "+tn_name["lastName"]
                tn_name=tn_name["userName"]

                eintrag.update({"tn_name":tn_name})
                eintrag.update({"klarname":tn_klarname})
                master_liste_gemeldete_nutzer.append(eintrag)

        threads = []
        for i in range(0,10):
            threads.append(Thread(target=nutzernamen_ziehen, args=(new_arrays[i],)))
            threads[-1].start()
        for thread in threads:
            thread.join()
    
        daten_gemeldete_nutzer=master_liste_gemeldete_nutzer
    

    headers2={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    freigabez??hler=0
    if len(daten_gemeldete_nutzer)<10:
        for eintrag2 in daten_gemeldete_nutzer:
                
            for eintrag3 in f??cher_id_array:            
                payload={

                    "LicenceId":eintrag2["licenceId"],
                    "ExaminationpartId":eintrag3,
                    "IsReleased":bool(1)

                }
                payload=json.dumps(payload)
                url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{eintrag2['userDetailId']}/releases/"
                r = requests.post(url, headers=headers2, data=payload)

                json_data = json.loads(r.text)
        
                if r.status_code==200:
                    freigabez??hler+=1
                    eel.progress_freigegebene_pr??fungen(1)

                    for eintrag in personen_webex_meeting:
                        if eintrag2["klarname"] == eintrag[0]:
                            eintrag[2]="??????"

                else:
                    pass
    
    if len(daten_gemeldete_nutzer)>=10:
        pieces = 10
        new_arrays = np.array_split(daten_gemeldete_nutzer, pieces)

        def freigabe_thread(array):
            global freigabez??hler
            for eintrag2 in array:
                for eintrag3 in f??cher_id_array:            
                    payload={

                        "LicenceId":eintrag2["licenceId"],
                        "ExaminationpartId":eintrag3,
                        "IsReleased":bool(1)

                    }
                    payload=json.dumps(payload)
                    url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{eintrag2['userDetailId']}/releases/"
                    r = requests.post(url, headers=headers2, data=payload)

                    json_data = json.loads(r.text)
            
                    if r.status_code==200:
                        freigabez??hler+=1
                        eel.progress_freigegebene_pr??fungen(1)

                        for eintrag in personen_webex_meeting:
                            if eintrag2["klarname"] == eintrag[0]:
                                eintrag[2]="??????"

                    else:
                        pass

        threads = []
        for i in range(0,10):
            threads.append(Thread(target=freigabe_thread, args=(new_arrays[i],)))
            threads[-1].start()
        for thread in threads:
            thread.join()  


    personen_webex_meeting.sort()
    
    excel_download_liste=daten_gemeldete_nutzer
    
    if personen_webex_meeting!=[]:
        for eintrag in excel_download_liste:
            for i in personen_webex_meeting:
                if eintrag["klarname"] == i[0]: 
                    eintrag["Webex anwesend"]="Ja"
                    eintrag["Pr??fung freigegeben"]="Ja"

                else:
                    eintrag["Webex anwesend"]="Nein"
                    eintrag["Pr??fung freigegeben"]="Ja"
    else:
        for eintrag in excel_download_liste:
            eintrag["Webex anwesend"]="Nein"
            eintrag["Pr??fung freigegeben"]="Ja"

    return personen_webex_meeting,freigabez??hler

@eel.expose
def anzeige_freigabeauswahl_confirm(lizenz_id_??bersicht,f??cher_id_array_??bersicht):
    text=f"Auswahl: \nLizenz: {lizenz_id_??bersicht}"
    for i in f??cher_id_array_??bersicht:
        text=text+f"\n      - Fach: {i}"
    
    return text


@eel.expose
def alle_pr??fungen_zur??ckziehen(lizenz_id_??bersicht,f??cher_id_array_??bersicht_zur??ckziehen):
    global freigabez??hler_zur??ckziehen,freigabez??hler_zur??ckziehen_tats??chlich
    
    while "|" in lizenz_id_??bersicht:
        lizenz_id_??bersicht=lizenz_id_??bersicht[1:]

    z??hler=-1
    for eintrag in f??cher_id_array_??bersicht_zur??ckziehen:
        z??hler+=1
        while "|" in f??cher_id_array_??bersicht_zur??ckziehen[z??hler]:
            f??cher_id_array_??bersicht_zur??ckziehen[z??hler]=f??cher_id_array_??bersicht_zur??ckziehen[z??hler][1:]

    token=oauth_lplus(benutzername,passwort)
    headers={
    "Authorization": f"Bearer {token}"
    }
    r = requests.get(f"https://fub.lplus-teststudio.de/publicapi/v1/licences/{lizenz_id_??bersicht}/candidateRelations", 
    headers=headers)

    daten_gemeldete_nutzer=json.loads(r.text)


    headers2={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    freigabez??hler_zur??ckziehen=0
    freigabez??hler_zur??ckziehen_tats??chlich=0

    if len(daten_gemeldete_nutzer)<10:
        for eintrag2 in daten_gemeldete_nutzer:
                
            for eintrag3 in f??cher_id_array_??bersicht_zur??ckziehen:            
                payload={

                    "LicenceId":eintrag2["licenceId"],
                    "ExaminationpartId":eintrag3,
                    "IsReleased":bool(0)

                }
                payload=json.dumps(payload)
                url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{eintrag2['userDetailId']}/releases/"
                r = requests.post(url, headers=headers2, data=payload)

                json_data = json.loads(r.text)
                
                if r.status_code==200:
                    freigabez??hler_zur??ckziehen+=1
                    eel.progress_abgerufene_personen_zur??ckziehen(1)
                    if json_data["countResettedExamRelease"]!=0:
                        freigabez??hler_zur??ckziehen_tats??chlich+=1
                        eel.progress_zur??ckgezogene_pr??fungen(1)
                
                    

                else:
                    pass


    if len(daten_gemeldete_nutzer)>=10:
        pieces = 10
        new_arrays = np.array_split(daten_gemeldete_nutzer, pieces)

        def zur??ckziehen(array):
            global freigabez??hler_zur??ckziehen,freigabez??hler_zur??ckziehen_tats??chlich
            for eintrag2 in array:
                    
                for eintrag3 in f??cher_id_array_??bersicht_zur??ckziehen:            
                    payload={

                        "LicenceId":eintrag2["licenceId"],
                        "ExaminationpartId":eintrag3,
                        "IsReleased":bool(0)

                    }
                    payload=json.dumps(payload)
                    url= f"https://fub.lplus-teststudio.de/publicapi/v1/candidate/{eintrag2['userDetailId']}/releases/"
                    r = requests.post(url, headers=headers2, data=payload)

                    json_data = json.loads(r.text)
            
                    if r.status_code==200:
                        freigabez??hler_zur??ckziehen+=1
                        eel.progress_abgerufene_personen_zur??ckziehen(1)
                        if json_data["countResettedExamRelease"]!=0:
                            freigabez??hler_zur??ckziehen_tats??chlich+=1
                            eel.progress_zur??ckgezogene_pr??fungen(1)

                    else:
                        pass

        threads = []
        for i in range(0,10):
            threads.append(Thread(target=zur??ckziehen, args=(new_arrays[i],)))
            threads[-1].start()
        for thread in threads:
            thread.join()

@eel.expose
def zur??ckziehen_??bersicht(lizenz_id_??bersicht,f??cher_id_array_??bersicht_zur??ckziehen):
    print(lizenz_id_??bersicht,f??cher_id_array_??bersicht_zur??ckziehen)

    text=f"Sollen alle Teilnehmer:innen f??r folgende Auswahl zur??ckgezogen werden: \nLizenz: {lizenz_id_??bersicht}"
    for i in f??cher_id_array_??bersicht_zur??ckziehen:
        text=text+f"\n      - Fach: {i}"
    
    return text

@eel.expose
def excelliste_generieren(meeting_auswahl):
    header = ['Name', 'Matrikelnummer', 'In Webex anwesend',"Pr??fung freigegeben"]
    datum=datetime.now().strftime("%Y-%m-%d")
    meeting_name_csv=f"Meeting_{meeting_auswahl}_{datum}.csv"
    
    #for eintrag in excel_download_liste:
    if len(excel_download_liste[0])>4:
        with open(meeting_name_csv, 'w+', newline='') as myfile:
            wr = csv.writer(myfile,delimiter=";")
            wr.writerow(header)
            for eintrag in excel_download_liste:
                daten=[eintrag["klarname"],eintrag["matrikelnummer"],eintrag["Webex anwesend"],eintrag["Pr??fung freigegeben"]]
                wr.writerow(daten)

    elif len(excel_download_liste[0])<=4:
        with open(meeting_name_csv, 'w+', newline='') as myfile:
            wr = csv.writer(myfile,delimiter=";")
            wr.writerow(header)
            for eintrag in excel_download_liste:

                if "??????" in eintrag:
                    anwesend="Ja"
                else:
                    anwesend="Nein"
                
                if eintrag[-1]=="???":
                    eintrag[-1]=""

                daten=[eintrag[0],eintrag[-1],anwesend]

                wr.writerow(daten)

    erfolgreich=True
    return erfolgreich


eel.start("index.html",size=(1200, 830))
