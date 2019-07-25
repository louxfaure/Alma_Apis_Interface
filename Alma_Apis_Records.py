import os
# external imports
import requests
import json
import logging
# internal import
from mail import mail
from logs import logs


__version__ = '0.1.0'
__api_version__ = 'v1'
__apikey__ = os.getenv('ALMA_API_KEY')
__region__ = os.getenv('ALMA_API_REGION')

ENDPOINTS = {
    'US': 'https://api-na.hosted.exlibrisgroup.com',
    'EU': 'https://api-eu.hosted.exlibrisgroup.com',
    'APAC': 'https://api-ap.hosted.exlibrisgroup.com'
}

FORMATS = {
    'json': 'application/json',
    'xml': 'application/xml'
}

RESOURCES = {
    'get_holding' : 'bibs/{bib_id}/holdings/{holding_id}'
}


class AlmaRecords(object):
    """A set of function for interact with Alma Apis in aréa "Records & Inventory"
    """

    def __init__(self, apikey=__apikey__, region=__region__,service='AlmaPy'):
        if apikey is None:
            raise Exception("Please supply an API key")
        if region not in ENDPOINTS:
            msg = 'Invalid Region. Must be one of {}'.format(list(ENDPOINTS))
            raise Exception(msg)
        self.apikey = apikey
        self.endpoint = ENDPOINTS[region]
        self.service = service
        self.logger = logging.getLogger(service)

    @property
    #Construit la requête et met en forme les réponses
    def baseurl(self):
        """Construct base Url for Alma Api
        
        Returns:
            strng -- Alma Base URL
        """
        return '{}/almaws/{}/'.format(self.endpoint, __api_version__)

    def fullurl(self, resource, ids={}):
        return self.baseurl + RESOURCES[resource].format(**ids)

    def headers(self, accept='json', content_type=None):
        headers = {
            "User-Agent": "pyalma/{}".format(__version__),
            "Authorization": "apikey {}".format(self.apikey),
            "Accept": FORMATS[accept]
        }
        if content_type is not None:
            headers['Content-Type'] = FORMATS[content_type]
        return headers

    def request(self, httpmethod, resource, ids, params={}, data=None,
                accept='json', content_type=None):
        response = requests.request(
            method=httpmethod,
            headers=self.headers(accept=accept, content_type=content_type),
            url=self.fullurl(resource, ids),
            params=params,
            data=data)
        try:
            response.raise_for_status()  
        except requests.exceptions.HTTPError:
            status = 'Error'
            self.logger.error("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            error_msg = "PPN inconnu ou service indisponible"
            return status, response.text
        return "Success", response

    def extract_content(self, response):
        ctype = response.headers['Content-Type']
        if 'json' in ctype:
            return response.json()
        else:
            return response.content.decode('utf-8')

    #Retourne une holding à partir de son identifiant et de l'identifiant de la notice bib
    def get_holding(self, bib_id, holding_id, accept='xml'):
        status,response = self.request('GET', 'get_holding',
                                {'bib_id' : bib_id,
                                'holding_id' : holding_id},
                                accept=accept)
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)
    
    def set_holding(self, bib_id, holding_id, data):
        status, response = self.request('PUT', 'get_holding', 
                                {'bib_id': bib_id,'holding_id': holding_id},
                                data=data, content_type='xml', accept='xml')
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)

