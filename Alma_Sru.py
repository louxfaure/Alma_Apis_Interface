import os
# external imports
import requests
import xml.etree.ElementTree as ET
import logging
import urllib.parse
# internal import
from mail import mail
from logs import logs




ns = {'sru': 'http://www.loc.gov/zing/srw/',
        'marc': 'http://www.loc.gov/MARC21/slim' }


class AlmaSru(object):

    def __init__(self, institution ='network',service='AlmaSru'):
        self.logger = logging.getLogger(service)
        self.institution = institution
        self.service = service

    @property

    def baseurl(self):
        return "https://pudb-{}.alma.exlibrisgroup.com/view/sru/{}?version=1.2&operation=searchRetrieve".format(self.institution.lower(),"33PUDB_"+self.institution.upper())

    def fullurl(self, query, reponseFormat,index,noticesSuppr,complex_query):
        return self.baseurl + '&format=' + reponseFormat + '&query=' + self.searchQuery(query, index, noticesSuppr, complex_query)

    def searchQuery(self, query, index, noticesSuprr, complex_query):
        if complex_query :
            searchQuery = query
        else :
            searchQuery = index
            searchQuery += '='
            searchQuery += query
        if not noticesSuprr:
            searchQuery += ' and alma.mms_tagSuppressed=false'
        return urllib.parse.quote(searchQuery)

    def sru_request(self, query ,reponseFormat='marcxml', index='alma.all_for_ui',noticesSuppr=False, complex_query=False):
        url=self.fullurl(query,reponseFormat, index,noticesSuppr,complex_query)
        self.logger.debug("{} :: alma_sru :: {}".format(query,url))
        r = requests.get(url)
        try:
            r.raise_for_status()  
        except requests.exceptions.HTTPError:
            raise HTTPError(r,self.service)
        reponse = r.content.decode('utf-8')
        reponsexml = ET.fromstring(reponse)
        return reponsexml

    def get_nombre_resultats(self,reponsexml):
        
        if reponsexml.find("sru:numberOfRecords",ns).text:
            return reponsexml.find("sru:numberOfRecords",ns).text
        else : 
            return 0
    
    def get_mmsId(self,record):
        return record.find("sru:recordIdentifier",ns).text

    def get_holdingId(self,record,libraryId):
        holdingList = []
        for holding in record.findall(".//marc:datafield[@tag='AVA']",ns):
            if holding.find("marc:subfield[@code='b']",ns).text == libraryId :
                holdingList.append(holding.find("marc:subfield[@code='8']",ns).text)
        return holdingList

    def ppnToMmsid(self, query ):
        reponse = self.sru_request(query=query ,reponseFormat='marcxml', index='alma.other_system_number')
        if  self.get_nombre_resultats(reponse) == '1' :
            mmsId = self.get_mmsId(reponse.find("sru:records/sru:record",ns))
            return mmsId
        else :
            return 'Ko'
    
    def originatingSystemIdToMmsid(self, origanitingSystemId ):
        query = "alma.mms_originatingSystemId={0} or alma.other_system_number={0}".format(origanitingSystemId)
        reponse = self.sru_request(query=query ,reponseFormat='marcxml', index='None', complex_query = True)
        if  self.get_nombre_resultats(reponse) == '1' :
            mmsId = self.get_mmsId(reponse.find("sru:records/sru:record",ns))
            return mmsId
        else :
            return 'Ko'
    def ppn_to_holding_id(self, ppn, library_id):
        """
        For a given PPN & a given library's id return a list of alma holdings'id
        
        Arguments:
            ppn {string} -- ppn de la notice. Préfixé par (PPN)
            library_id {string} -- Alma library id
        
        Returns:
            string -- status of reponse (Ok if one result, Ko if 0 or >1 record or if no holding)
            string -- error_msg or number of result
            string -- mms id of Alma record
            list -- list of holding id
        """
        reponse = self.sru_request(query=ppn ,reponseFormat='marcxml', index='alma.other_system_number')
        nb_result = self.get_nombre_resultats(reponse)
        if  nb_result != '1' :
            self.logger.error("{} :: AlmaSru.ppn_to_holding_id :: {} notices dans Alma".format(ppn, nb_result))
            error_msg = "{} notices dans Alma pour le ppn {}".format(nb_result, ppn)
            return 'Ko', error_msg, 0, 0
        else :
            mms_id = self.get_mmsId(reponse.find("sru:records/sru:record",ns))
            holdingIdList = self.get_holdingId(reponse.find("sru:records/sru:record/sru:recordData/marc:record",ns),library_id)
            self.logger.debug("{} :: AlmaSru.ppn_to_holding_id :: {} holdings dans Alma pour le mms id {}".format(ppn, len(holdingIdList), mms_id))
            if len(holdingIdList) == 0:
                self.logger.error("{} :: AlmaSru.ppn_to_holding_id :: Aucune holding dans Alma pour le mms id {}".format(ppn, mms_id))
                error_msg = "Aucune holding dans Alma"
                return 'Ko', error_msg, 0, 0
            else:
                return 'Ok', nb_result, mms_id, holdingIdList
            
#Gestion des erreurs
class HTTPError(Exception):

    def __init__(self, response, service):
        super(HTTPError,self).__init__(self.msg(response, service))

    def msg(self, response, service):
        logger = logging.getLogger(service)
        msg = "\n  HTTP Status: {}\n  Method: {}\n  URL: {}\n  Response: {}"
        sujet = service + 'Erreur'
        message = mail.Mail()
        message.envoie(os.getenv('ADMIN_MAIL'),os.getenv('ADMIN_MAIL'),sujet, msg.format(response.status_code, response.request.method, response.url, response.text) )
        logger.error("HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code, response.request.method,
                          response.url, response.text))