#!/usr/bin/python3
# -*- coding: utf-8 -*-

import Alma_Apis
import os
import json



def get_job(job_id,instance_id):
    #Interroge un job toutes les 2 minutes et retourne le rapport quand ce dernier est terminé
    detail_service = api.get_job_instances(job_id,instance_id)
    statut = detail_service['status']['value']
    # log_module.debug("[get_job (Job ({}) Instance ({}))] Statut ({})".format(job_id,instance_id, statut))
    
    if statut=='RUNNING' or statut=='INITIALIZING':
        progression=detail_service['progress']
        # log_module.info("[get_job (Job ({}) Instance ({}))] Traitement en cours déxecution ({}%)".format(job_id,instance_id,progression))
        time.sleep(120)
        get_job(job_id,instance_id)
    elif statut == 'COMPLETED_SUCCESS':
        return detail_service
    else:
        # log_module.error("[get_job (Job ({}) Instance ({}))] Statut ({}) Inconnu !".format(job_id,instance_id, statut))
        raise Exception("Statut du job inconnu !") 

#On initialise l'objet API
api = Alma_Apis.Alma(apikey=os.getenv('PROD_NETWORK_CONF_API'), region='EU', service='test')
suppr_bib_job_rapport = get_job('M28',4070270680004671)
# print(json.dumps(identifie_bib_job_rapport, indent=4, sort_keys=True))
set_name = suppr_bib_job_rapport['counter'][0]['value']

if suppr_bib_job_rapport['counter'][0]['value'] == 'The report was not generated due to the number of records required to be calculated':
    text = 'The report was not generated due to the number of records required to be calculated'
else:   
    text = '''Service Delete_Bib terminé avec succès.
    Sur {} notice(s) sans inventaire :
        * {} notice(s) supprimée(s)
        * {} notice(s) non supprimée(s) car liées à un inventaire
        * {} notice(s) non supprimée(s) car liées à une commande
        * {} notice(s) non supprimée(s) car liées à d'autres notices\
    '''.format(number_of_set_members,
            suppr_bib_job_rapport['counter'][0]['value'],
            suppr_bib_job_rapport['counter'][1]['value'],
            suppr_bib_job_rapport['counter'][2]['value'],
            suppr_bib_job_rapport['counter'][3]['value'])
# print(number_of_set_members)
print(text)