import os
# external imports
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import logging
import xml.etree.ElementTree as ET
import time
import sys
from math import *

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
    'service' : 'electronic/e-collections/{ecollection_id}/e-services/{eservice_id}',
    'portfolios_list' : 'electronic/e-collections/{ecollection_id}/e-services/{eservice_id}/portfolios?limit={limit}&offset={offset}',
    'portfolio' : 'electronic/e-collections/{ecollection_id}/e-services/{eservice_id}/portfolios/{portfolio_id}'
}

NS = {'sru': 'http://www.loc.gov/zing/srw/',
        'marc': 'http://www.loc.gov/MARC21/slim',
        'xmlb' : 'http://com/exlibris/urm/general/xmlbeans'
         }

class AlmaERecords(object):
    """A set of function for interact with Alma Apis in area "Electronic"
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
            string -- Alma Base URL
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
    def get_error_message(self, response, accept):
        """Extract error code & error message of an API response
        
        Arguments:
            response {object} -- API REsponse
        
        Returns:
            int -- error code
            str -- error message
        """
        error_code, error_message = '',''
        if accept == 'xml':
            root = ET.fromstring(response.text)
            error_message = root.find(".//xmlb:errorMessage",NS).text if root.find(".//xmlb:errorMessage",NS).text else response.text 
            error_code = root.find(".//xmlb:errorCode",NS).text if root.find(".//xmlb:errorCode",NS).text else '???'
        else :
            content = response.json()
            error_message = content['errorList'][0]['errorMessage']
            errorCode = content['errorList'][0]['errorCode']
        return error_code, error_message
    
    def request(self, httpmethod, resource, ids, params={}, data=None,
                accept='json', content_type=None, nb_tries=0, in_url=None):
        #20190905 retry request 3 time s in case of requests.exceptions.ConnectionError
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.request(
            method=httpmethod,
            headers=self.headers(accept=accept, content_type=content_type),
            url= self.fullurl(resource, ids) if in_url is None else in_url,
            params=params,
            data=data)
        try:
            response.raise_for_status()  
        except requests.exceptions.HTTPError:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            return 'Error', "{} -- {}".format(error_code, error_message)
        except requests.exceptions.ConnectionError:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            return 'Error', "{} -- {}".format(error_code, error_message)
        except requests.exceptions.RequestException:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            return 'Error', "{} -- {}".format(error_code, error_message)
        return "Success", response

            

    
    def extract_content(self, response):
        ctype = response.headers['Content-Type']
        if 'json' in ctype:
            return response.json()
        else:
            return response.content.decode('utf-8')


    #Retourne une holding à partir de son identifiant et de l'identifiant de la notice bib
    def get_eservice(self, ecollection_id, eservice_id, accept='json'):
        """ Appelle un service 

        Args:
            ecollection_id (int): Collection id 
            eservice_id (int): Service ID
            accept (str, optional): data format . xml or json. Defaults to 'json'.

        Returns:
            status : Success or Error
            response :xml string or json object. If status is Errorr return Error msg.
        """
        status,response = self.request('GET', 'service',
                                {'ecollection_id' : ecollection_id,
                                'eservice_id' : eservice_id},
                                accept=accept)
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)

    def get_number_of_portfolios_for_eservice(self, ecollection_id, eservice_id, accept='json'):
        """ Appelle un service et returne le nombre de portfolio lié

        Args:
            ecollection_id (int): Collection id 
            eservice_id (int): Service ID
            accept (str, optional): data format . xml or json. Defaults to 'json'.

        Returns:
            status : Success or Error
            response :Nb des portfolios. If status is Errorr return Error msg.
        """
        status,response = self.get_eservice(ecollection_id, eservice_id, accept='json')
        if status == 'Error':
            return status, response
        else:
            return status, response['portfolios']['value']

    def get_portfolios_list(self, ecollection_id, eservice_id, limit=100, offset=0, accept='json'):
        """ Appelle un service et retourne le nombre de portfolio lié
        Args:
            ecollection_id (int): Collection id 
            eservice_id (int): Service ID
            limit (int) : Limits the number of results. Optional. Valid values are 0-100. Default value: 10.
            offset(int) : Offset of the results returned. Optional. Default value: 0, which means that the first results will be returned.
            accept (str, optional): data format . xml or json. Defaults to 'json'.

        Returns:
            status : Success or Error
            response : .If status is Errorr return Error msg.
        """
        status,response = self.request('GET', 'portfolios_list',
                                {'ecollection_id' : ecollection_id,
                                'eservice_id' : eservice_id,
                                'offset' : offset,
                                'limit' : limit},
                                accept=accept)
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)

    

        
        
        
    

