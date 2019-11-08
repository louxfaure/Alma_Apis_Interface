#!/usr/bin/python3
# -*- coding: utf-8 -*-

import Alma_Sru
import Alma_Apis_Users
import xml.etree.ElementTree as ET

import os
# Retourne l'état de collection d'une notice (ppn) pour une bibliothèque (RCR)
# Si plusieurs ou 0 retyourne faux 

libraryId = '1103300000'
rcr = '335222203'
ppn ='039550117'
sru = Alma_Sru.AlmaSru(institution='ub',service='test')
api = Alma_Apis.Alma(apikey=os.getenv('TEST_UB_API'), region='EU', service='test')

mmsId, holdingIdList = sru.ppnToHoldingid(query='(PPN)'+ppn,libraryId=libraryId)
print(mmsId)
etatColUnique, etatCollSudoc = retrouve_etat_col(rcr,ppn)
if etatColUnique :
    print("{} : {}".format(ppn,etatCollSudoc))
    for holdingId in holdingIdList :
        print(holdingId)
        holding = api.get_holding(mmsId, holdingId, accept='xml')
        newHolding = construit_new_holding(holding,etatCollSudoc)     
        reponse = api.set_holding(mmsId, holdingId, newHolding)
        print(reponse)
else :
    print(etatCollSudoc)