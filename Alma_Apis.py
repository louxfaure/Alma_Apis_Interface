import os
# external imports
import requests
import json
# internal import
from . import records
from mail import mail


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
    'bib': 'bibs/{mms_id}',
    'holdings': 'bibs/{mms_id}/holdings',
    'holding': 'bibs/{mms_id}/holdings/{holding_id}',
    'items': 'bibs/{mms_id}/holdings/{holding_id}/items',
    'item': 'bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}',
    'bib_requests': 'bibs/{mms_id}/requests',
    'item_requests':
        'bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}/requests',
    'bib_requests': 'bibs/{mms_id}/requests',
    'bib_request': 'bibs/{mms_id}/requests/{request_id}',
    'item_requests': 'bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}/requests',
    'item_request': 'bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}/requests/{request_id}',
    'bib_booking_availability': 'bibs/{mms_id}/booking-availability',
    'item_booking_availability':
        'bibs/{mms_id}/holdings/{holding_id}/items/' +
        '{item_pid}/booking-availability',
    'loan': 'bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}/loans',
    'job' : 'conf/jobs/{job_id}?op={operation}',
    'job_instance' : 'conf/jobs/{job_id}/instances/{instance_id}',
    'search_set_id' : 'conf/sets?q=name~{set_name}'
}


class Alma(object):

    def __init__(self, apikey=__apikey__, region=__region__,service='AlmaPy'):
        if apikey is None:
            raise Exception("Please supply an API key")
        if region not in ENDPOINTS:
            msg = 'Invalid Region. Must be one of {}'.format(list(ENDPOINTS))
            raise Exception(msg)
        self.apikey = apikey
        self.endpoint = ENDPOINTS[region]
        self.service = service

    @property
    #Construit la requête et met en forme les réponses
    def baseurl(self):
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
            raise HTTPError(response,self.service)
        return response

    def extract_content(self, response):
        ctype = response.headers['Content-Type']
        if 'json' in ctype:
            return response.json()
        else:
            return response.content.decode('utf-8')

    #Exécute un traitement
    def post_job(self, job_id, data, content_type='json', accept='json'):
        response = self.request('POST', 'job', 
                                {'job_id': job_id,'operation':'run'},
                                data=data, content_type=content_type, accept=accept)
        return self.extract_content(response)

    #Appel un traitement à l'aide de l'identifiant et l'instance du traitement
    def get_job_instances(self, job_id, instance_id, accept='json'):
        response = self.request('GET', 'job_instance',
                                {'job_id': job_id,
                                 'instance_id': instance_id},
                                accept=accept)
        return self.extract_content(response)
    
    #Retourne l'identifiant d'un jeu de résultat à partir du nom de ce dernier
    def get_set_id(self, set_name, accept='json'):
        query = set_name.replace(" ", "_")
        response = self.request('GET', 'search_set_id',
                                {'set_name': query},
                                accept=accept)
        content = self.extract_content(response)
        try:
            set_id = content['set'][0]['id']
        except KeyError:
            raise HTTPError(response,self.service)
        return set_id

#Gestion des erreurs
class HTTPError(Exception):

    def __init__(self, response, service):
        super(HTTPError,self).__init__(self.msg(response, service))

    def msg(self, response, service):
        msg = "\n  HTTP Status: {}\n  Method: {}\n  URL: {}\n  Response: {}"
        sujet = service + 'Erreur'
        message = mail.Mail()
        message.envoie('alexandre.faure@u-bordeaux.fr','alexandre.faure@u-bordeaux.fr',sujet, msg.format(response.status_code, response.request.method, response.url, response.text) )
        return msg.format(response.status_code, response.request.method,
                          response.url, response.text)
