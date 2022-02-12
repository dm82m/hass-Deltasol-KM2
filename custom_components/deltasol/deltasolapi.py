"""
Gets sensor data from Resol Deltasol KM2/DL2/DL3 using api.
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2
"""
import requests
import datetime
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
        self.api_mode = None

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


    def detect_mode(self):
        if self.api_mode is not None:
            return self.api_mode
        
        try:
            dlxurl = f"http://{self.host}/dlx/"
            _LOGGER.debug(f"Testing DLX {dlxurl}")
            response = requests.request("GET", dlxurl)
            _LOGGER.debug(f"DLX response {response}")
            _LOGGER.debug(f"Detected DLX")
            self.api_mode = 'dlx'
            return self.api_mode

        except ValueError:
            _LOGGER.debug("Unable to detect DLX")

        _LOGGER.debug("Testing KM2")
        # find way to test for km2
        _LOGGER.debug(f"Detected KM2")
        self.api_mode = 'km2'
        return self.api_mode


    def fetch_data(self):
        """Use api to get data"""
        mode = self.detect_mode()

        response = {}

        if(mode=='km2'):
            response = self.fetch_data_km2()
        elif(mode=='dlx'):
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