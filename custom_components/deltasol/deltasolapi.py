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

    def __init__(self, username, password, host, api_mode="km2"):
        self.data = None
        self.host = host
        self.username = username
        self.password = password
        self.api_mode = api_mode


    def __parse_data(self, response):
        icon_mapper = defaultdict(lambda: "mdi:flash")
        icon_mapper['°C'] = "mdi:thermometer"

        data = {}

        j = 0
        for i in response["headers"][0]["fields"]:
            value = response["headersets"][0]["packets"][0]["field_values"][j]["raw_value"]
            if isinstance(value, float):
              value = round(value, 2)
            unit = i["unit"].strip()
            data[i["name"].replace(" ", "_").lower()] = (value, icon_mapper[unit], unit)
            j += 1

        return data


    def fetch_data(self):
        """Use api to get data"""

        response = {}
        
        if self.api_mode == "km2":
            url = "http://" + self.host + "/cgi-bin/resol-webservice"

            headers = {
              'Content-Type': 'application/json'
            }

            payload = "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '" + self.username + "','password': '" + self.password + "'}}]"
            response = requests.request("POST", url, headers=headers, data = payload).json()
            
            authId = response[0]['result']['authId']
            
            payload = "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '" + authId + "'}}]"
            response = requests.request("POST", url, headers=headers, data = payload).json()
            response = response[0]["result"]
            
        elif self.api_mode == "dlx":
            url = f'http://{self.host}/dlx/download/live?sessionAuthUsername={self.username}&sessionAuthPassword={self.password}'
            response = requests.request("GET", url).json()

        return self.__parse_data(response)
