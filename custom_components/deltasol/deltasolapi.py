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
        self.product= None

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
            _LOGGER.debug(f"Detecting resol product {url}")
            response = requests.request("GET", url)
            if(response.status_code == 200):
                _LOGGER.debug(f"response {response.text}")
                matches = re.search(r'product\s=\s["](.*?)["]', response.text)
                if matches:
                    self.product = matches.group(1).lower()
                else:
                     self.product = "km2"
                _LOGGER.debug(f"Detected {self.product}")
                return self.product
                
        except Exception as e:
            _LOGGER.debug(f"Error detecting resol product - {e}")

        _LOGGER.warning("Unable to detect resol system")
        return self.product


    def fetch_data(self):
        """Use api to get data"""
        product = self.detect_product()

        response = {}

        if(product=='km2'):
            response = self.fetch_data_km2()
        elif(product=='dl2' or product=='dl3'):
            response = self.fetch_data_dlx()
        else:
            _LOGGER.debug("Invalid mode, unable to retrive data")

        return self.__parse_data(response)


    def fetch_data_km2(self):
        _LOGGER.debug("Retriving data from km2")
        response = {}
        url = f"http://{self.host}/cgi-bin/resol-webservice"

        headers = {
            'Content-Type': 'application/json'
        }

        payload = "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '" + self.username + "','password': '" + self.password + "'}}]"
        response = requests.request("POST", url, headers=headers, data = payload).json()

        _LOGGER.debug("Got valid JSON, assuming that we have a KM2 device ...")

        authId = response[0]['result']['authId']
        
        payload = "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '" + authId + "'}}]"

        response = requests.request("POST", url, headers=headers, data = payload).json()
        _LOGGER.debug(f"KM2 response {response}")
        response = response[0]["result"]
        return response


    def fetch_data_dlx(self):
        _LOGGER.debug("Retriving data from dlx")
        response = {}

        filter = f"filter={self.api_key}&" if self.api_key else ""
        
        url = f"http://{self.host}/dlx/download/live?{filter}sessionAuthUsername={self.username}&sessionAuthPassword={self.password}"
        _LOGGER.debug(f"DLX requesting sensor data url {url.replace(self.password, '******')}")
        
        response = requests.request("GET", url).json()
        _LOGGER.debug(f"DLX response {response}")
        return response