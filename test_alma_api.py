#!/usr/bin/python3
# -*- coding: utf-8 -*-

import Alma_Apis
import os

#On initialise l'objet API
api = Alma_Apis.Alma(apikey=os.getenv('TEST_NETWORK_API'), region='EU', service='test')

number_of_se_members = api.get_set_member_number(2982907310004671)
print(number_of_se_members)