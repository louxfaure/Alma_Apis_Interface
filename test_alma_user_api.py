#!/usr/bin/python3
# -*- coding: utf-8 -*-
import Alma_Apis_Users
import xml.etree.ElementTree as ET
import json

import os
# Retourne l'état de collection d'une notice (ppn) pour une bibliothèque (RCR)
# Si plusieurs ou 0 retyourne faux 

def get_user_institution(user_id):
    """Retourne la liste des institutions où le compte du lecteur est présent. Pour cahque institution retourne le nombre de prêt
    
    Arguments:
        user_id {str} -- identifiant du lecteur
    """
    # institutions_list = ['NETWORK','UB','UBM','IEP','INP','BXSA']
    institutions_list = ['NETWORK','UB','BXSA']
    users_list = []
    for institution in institutions_list :
        api_key = os.getenv("TEST_{}_API".format(institution))
        api = Alma_Apis_Users.AlmaUsers(apikey=api_key, region='EU', service='test')
        status, response = api.retrieve_user_by_id(user_id, accept='json')
        # print("{} --> {} : {}".format(institution,status,response))
        if status == "Success":
            total_record_count = response['total_record_count']
            if total_record_count == 1 :
                user_data = {}
                status,user = api.get_user(user_id,accept='json')
                user_data["institution"] = institution
                user_data["data"] = user
                users_list.append(user_data)
    return users_list

        

user_id = 'afaure001003@u-bordeaux.fr'
request_id = '2726312110004672'
api_key = os.getenv("TEST_UB_API")
api = Alma_Apis_Users.AlmaUsers(apikey=api_key, region='EU', service='test')

status,response = api.delete_user_request(user_id,request_id,accept='json')
print(status)
print(response)
# response['primary_id'] = 'testyaaddi@u-bordeaux.fr'
# a,b = api.update_user(user_id,
#                     "user_group,job_category,pin_number,preferred_language,campus_code,rs_libraries,user_title,library_notices",
#                     json.dumps(response, indent=4, sort_keys=True),
#                     accept='json',
#                     content_type='json')
# print(b)          