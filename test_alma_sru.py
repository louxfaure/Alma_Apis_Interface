#!/usr/bin/python3
# -*- coding: utf-8 -*-
from Abes_Apis_Interface.AbesXml import AbesXml
import Alma_Sru
import Alma_Apis
import xml.etree.ElementTree as ET

import os
# Retourne l'état de collection d'une notice (ppn) pour une bibliothèque (RCR)
# Si plusieurs ou 0 retyourne faux 
def retrouve_etat_col(rcr,ppn):
    abes = AbesXml(ppn=ppn,service='test')
    etatsColl = abes.get_etat_col(rcr)
    if len(etatsColl) == 1:
        return True, etatsColl[0]
    elif len(etatsColl) == 0:
        return False, "Aucun état de collection dans le SUDOC pour cette revue ppn {}".format(ppn)
    else:
        return False, "{} états de collection dans le SUDOC pour cette revue ppn {}".format(len(etatsColl),ppn)

#Pour toutes les occurences de champs passés en paramètre (xml object),
#retourne la liste detoutes les valeurs d'un sous-champs dont le code est passé en paramètre 
def retourne_valeur_sschamps(champs,codeSsChamp):
    valeurs_sschamps = []
    for champ in champs:
        for ssChamp in champ.findall("subfield[@code='{}']".format(codeSsChamp)):
            valeurs_sschamps.append(ssChamp.text)
    return valeurs_sschamps

def cree_champ(tag,firstInd,secondInd):
    nouvChamp =  ET.Element("datafield")
    nouvChamp.set('ind1', firstInd)
    nouvChamp.set('ind2', secondInd)
    nouvChamp.set('tag', tag)
    return nouvChamp

def cree_sous_champ(code,valeur):
    nouvSSChamp =  ET.Element("subfield")
    nouvSSChamp.set('code', code)
    nouvSSChamp.text = valeur
    return nouvSSChamp


def construit_new_holding(holding, newEtaCol):
    root = ET.fromstring(holding)
    #On récupère les notes publiques (866 $$z)
    notesPubliques = retourne_valeur_sschamps(root.findall(".//datafield[@tag='866']"),"z")
    print(notesPubliques) 
    #On récupère les notes pro (866 $$x)
    notesPro = retourne_valeur_sschamps(root.findall(".//datafield[@tag='866']"),"x")
    print(notesPro) 
    #Backup des anciens Etats de colection en 901
    for champ in root.findall(".//datafield[@tag='866']"):
        champ.set('tag', '901')
    notice = root.find('.//record')
    newChpEtatCol = cree_champ('866',' ','0')
    newSsChpText = cree_sous_champ('a',newEtaCol)
    newChpEtatCol.append(newSsChpText)
    #On réinjecte les notes
    for note in notesPro :
        champNote = cree_sous_champ('x',note)
        newChpEtatCol.append(champNote)
    for note in notesPubliques :
        champNote = cree_sous_champ('z',note)
        newChpEtatCol.append(champNote)
    notice.append(newChpEtatCol)
    print(ET.tostring(root))


libraryId = '1103300000'
rcr = '335222203'
ppn ='039550117'
sru = Alma_Sru.AlmaSru(institution='ub',service='test')
api = Alma_Apis.Alma(apikey=os.getenv('TEST_UB_API'), region='EU', service='test')
# reponse = sru.ppnToMmsid(query='(PPN)168466783')
# print(reponse)
mmsId, holdingIdList = sru.ppnToHoldingid(query='(PPN)'+ppn,libraryId=libraryId)
print(mmsId)
etatColUnique, etatCollSudoc = retrouve_etat_col(rcr,ppn)
if etatColUnique :
    print("{} : {}".format(ppn,etatCollSudoc))
    for holdingId in holdingIdList :
        print(holdingId)
        holding = api.get_holding(mmsId, holdingId, accept='xml')
        newHolding = construit_new_holding(holding,etatCollSudoc)     
        # reponse = api.set_holding(mmsId, holdingId, ET.tostring(root))
        # print(reponse)
else :
    print(etatCollSudoc)