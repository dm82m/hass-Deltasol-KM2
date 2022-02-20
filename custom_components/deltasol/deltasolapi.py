"""
Gets sensor data from Resol Deltasol KM2/DL2/DL3 using api.
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2
"""
import requests
import datetime
import re
from collections import defaultdict

from .const import (
    _LOGGER
)

class DeltasolApi(object):
    """ Wrapper class for Deltasol KM2"""

    def __init__(self, username, password, host, api_key):
        self.data = None
        self.host = host
        self.username = username
        self.password = password
        self.api_key = api_key
        self.product = None

    def __parse_data(self, response):
        icon_mapper = defaultdict(lambda: "mdi:flash")
        icon_mapper['°C'] = "mdi:thermometer"

        data = {}

        iHeader = 0
        for header in response["headers"]:
            _LOGGER.debug(f"Found header[{iHeader}] now parsing it ...")
            iField = 0
            for field in response["headers"][iHeader]["fields"]:
                value = response["headersets"][0]["packets"][iHeader]["field_values"][iField]["raw_value"]
                if isinstance(value, float):
                    value = round(value, 2)
                unit = field["unit"].strip()
                data[field["name"].replace(" ", "_").lower()] = (value, icon_mapper[unit], unit)
                iField += 1
            iHeader +=1

        return data

    def detect_product(self):
        if self.product is not None:
            return self.product

        try:
            url = f"http://{self.host}/cgi-bin/get_resol_device_information"
            _LOGGER.info(f"Auto detecting Resol Deltasol product from {url}")
            response = requests.request("GET", url)
            if(response.status_code == 200):
                _LOGGER.debug(f"response: {response.text}")
                matches = re.search(r'product\s=\s["](.*?)["]', response.text)
                if matches:
                    self.product = matches.group(1).lower()
                    _LOGGER.info(f"Detected Resol Deltasol product: {self.product}")
                else:
                    _LOGGER.error("Your device was reachable but we could not correctly detect it, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose")
                    #TODO #12 grateful shutdown
            else:
                _LOGGER.error("Are you sure you entered the correct address of the Resol Deltasol KM2/DL2/DL3 device? Please re-check and if the issue still persists, please file an issue here: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose")
                #TODO #12 grateful shutdown
                
        except RequestException as e:
            _LOGGER.error(f"Error detecting Resol Deltasol product - {e}, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose")
            #TODO #12 grateful shutdown
            
        return self.product


    def fetch_data(self):
        """Use api to get data"""
        product = self.detect_product()

        response = {}

        if(product == 'km2'):
            response = self.fetch_data_km2()
        elif(product == 'dl2' or product == 'dl3'):
            response = self.fetch_data_dlx()
        else:
            _LOGGER.error(f"We detected your Resol Deltasol product as {product} and this product is currently not supported. If you want you can file an issue to support this device here: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose")
            #TODO #12 grateful shutdown

        return self.__parse_data(response)


    def fetch_data_km2(self):
        _LOGGER.debug("Retrieving data from km2")
        
        response = {}
        
        url = f"http://{self.host}/cgi-bin/resol-webservice"
        _LOGGER.debug(f"KM2 requesting sensor data url {url}")
                
        headers = {
            'Content-Type': 'application/json'
        }
        payload = "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '" + self.username + "','password': '" + self.password + "'}}]"
        response = requests.request("POST", url, headers=headers, data = payload).json()
        #TODO #13 handle wrong credentials and grateful shutdown
        authId = response[0]['result']['authId']
        
        payload = "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '" + authId + "'}}]"
        response = requests.request("POST", url, headers=headers, data = payload).json()
        _LOGGER.debug(f"KM2 response: {response}")
        response = response[0]["result"]
        
        return response


    def fetch_data_dlx(self):
        _LOGGER.debug("Retriving data from dlx")
        
        response = {}

        filter = f"filter={self.api_key}&" if self.api_key else ""
        
        url = f"http://{self.host}/dlx/download/live?{filter}sessionAuthUsername={self.username}&sessionAuthPassword={self.password}"
        _LOGGER.debug(f"DLX requesting sensor data url {url.replace(self.password, '***')}")
        
        response = requests.request("GET", url).json()
        #TODO #13 handle wrong credentials and grateful shutdown
        _LOGGER.debug(f"DLX response: {response}")
        return response
