"""
Gets sensor data from Deltasol KM2 using api.
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

    def __init__(self, username, password, host):
        self.data = None
        self.host = host
        self.username = username
        self.password = password

    def fetch_data(self):
        """Use api to get data"""

        url = "http://" + self.host + "/cgi-bin/resol-webservice"

        headers = {
          'Content-Type': 'application/json'
        }

        payload = "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '" + self.username + "','password': '" + self.password + "'}}]"
        response = requests.request("POST", url, headers=headers, data = payload).json()
        
        authId = response[0]['result']['authId']
        
        payload = "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '" + authId + "'}}]"
        response = requests.request("POST", url, headers=headers, data = payload).json()

        icon_mapper = defaultdict(lambda: "mdi:flash")
        icon_mapper['°C'] = "mdi:thermometer"
        
        data = {}
        
        j = 0
        for i in response[0]["result"]["headers"][0]["fields"]:
            value = response[0]["result"]["headersets"][0]["packets"][0]["field_values"][j]["raw_value"]
            if isinstance(value, float):
              value = round(value, 2)
            data[i["name"].replace(" ", "_").lower()] = (value, icon_mapper[i["unit"]], i["unit"])
            j += 1
            
        return data
