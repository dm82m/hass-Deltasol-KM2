"""API Placeholder.

You should create your api seperately and have it hosted on PYPI.  This is included here for the sole purpose
of making this example code executable.
"""

from dataclasses import dataclass
from enum import StrEnum
import requests
import datetime
import logging
import re
from random import choice, randrange
from collections import namedtuple
from homeassistant.exceptions import IntegrationError
from requests.exceptions import RequestException

_LOGGER = logging.getLogger(__name__)


class DeviceType(StrEnum):
    """Device types."""

    TEMP_SENSOR = "temp_sensor"
    DOOR_SENSOR = "door_sensor"
    OTHER = "other"


@dataclass
class Device:
    """API device."""

    device_id: int
    device_unique_id: str
    device_type: DeviceType
    name: str
    state: int | float | bool | str
    unit: str
    description: str
    bus_dest: str
    bus_src: str


class API:
    """Class for example API."""

    def __init__(self, host: str, port: int, user: str, pwd: str, api_key: str) -> None:
        """Initialise."""
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.api_key = api_key
        self.product = None
        self.connected: bool = False

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.host.replace(".", "_")

    def connect(self) -> bool:
        """Connect to api."""
        try:
            self.product = self.detect_product()
            self.connected = True
            return True
        except IntegrationError as error:
            raise APIConnectionError(str(error))

    def disconnect(self) -> bool:
        """Disconnect from api."""
        self.connected = False
        return True

    def get_devices(self) -> list[Device]:
        """Get devices on api."""
        return self.fetch_data()

    def __parse_data(self, response):
        data = []

        iHeader = 0
        for header in response["headers"]:
            _LOGGER.debug(f"Found header[{iHeader}] now parsing it ...")
            iField = 0
            for field in response["headers"][iHeader]["fields"]:
                value = response["headersets"][0]["packets"][iHeader]["field_values"][iField]["raw_value"]
                if isinstance(value, float):
                    value = round(value, 2)
                if "date" in field["name"]:
                    epochStart = datetime.datetime(2001, 1, 1, 0, 0, 0, 0)
                    value = epochStart + datetime.timedelta(0, value)
                data.append(
                    Device(
                        device_id=1,
                        device_unique_id = header["id"] + "__" + field["id"],
                        device_type = DeviceType.OTHER,
                        name=field["name"].replace(" ", "_").lower(),
                        state=value,
                        unit=field["unit"].strip(),
                        description=header["description"],
                        bus_dest=header["destination_name"],
                        bus_src=header["source_name"]
                    )
                )
                _LOGGER.info(data)
                iField += 1
            iHeader +=1

        return data

    def detect_product(self):
        if self.product is not None:
            return self.product
        try:
            url = f"http://{self.host}:{self.port}/cgi-bin/get_resol_device_information"
            _LOGGER.info(f"Auto detecting Resol product from {url}")
            response = requests.request("GET", url)
            if(response.status_code == 200):
                _LOGGER.debug(f"response: {response.text}")
                matches = re.search(r'product\s=\s["](.*?)["]', response.text)
                if matches:
                    self.product = matches.group(1).lower()
                    _LOGGER.info(f"Detected Resol product: {self.product}")
                else:
                    error = "Your device was reachable but we could not correctly detect it, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
                    _LOGGER.error(error)
                    raise IntegrationError(error)
            else:
                error = "Are you sure you entered the correct address of the Resol KM2/DL2/DL3 device? Please re-check and if the issue still persists, please file an issue here: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
                _LOGGER.error(error)
                raise IntegrationError(error)
        except RequestException as e:
            error = f"Error detecting Resol product - {e}, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
            _LOGGER.error(error)
            raise IntegrationError(error)
        return self.product

    def fetch_data(self):
        """ Use api to get data """

        try:
            product = self.detect_product()

            response = {}
            if(product == 'km2'):
                response = self.fetch_data_km2()
            elif(product == 'dl2' or product == 'dl3'):
                response = self.fetch_data_dlx()
            else:
                error = f"We detected your Resol product as {product} and this product is currently not supported. If you want you can file an issue to support this device here: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
                _LOGGER.error(error)
                raise IntegrationError(error)

            return self.__parse_data(response)

        except IntegrationError as error:
            raise error


    def fetch_data_km2(self):
        _LOGGER.debug("Retrieving data from km2")
        
        response = {}
        
        url = f"http://{self.host}:{self.port}/cgi-bin/resol-webservice"
        _LOGGER.debug(f"KM2 requesting sensor data url {url}")
                
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '" + self.user + "','password': '" + self.pwd + "'}}]"
            response = requests.request("POST", url, headers=headers, data = payload).json()
            authId = response[0]['result']['authId']
            
            payload = "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '" + authId + "'}}]"
            response = requests.request("POST", url, headers=headers, data = payload).json()
            _LOGGER.debug(f"KM2 response: {response}")
            response = response[0]["result"]

        except KeyError:
            error = "Please re-check your username and password in your configuration!"
            _LOGGER.error(error)
            raise IntegrationError(error)
        
        return response


    def fetch_data_dlx(self):
        _LOGGER.debug("Retrieving data from dlx")
        
        response = {}

        url = f"http://{self.host}:{self.port}/dlx/download/live"
        debugMessage = f"DLX requesting sensor data url {url}"
        
        if self.user is not None and self.pwd is not None:
            auth = f"?sessionAuthUsername={self.user}&sessionAuthPassword={self.pwd}"
            filter = f"&filter={self.api_key}" if self.api_key else ""
            url = f"{url}{auth}{filter}"
            debugMessage = f"DLX requesting sensor data url {url.replace(self.pwd, '***')}"
            
        _LOGGER.debug(debugMessage)
        
        response = requests.request("GET", url)

        if(response.status_code == 200):
            response = response.json()
        else:
            error = "Please re-check your username and password in your configuration!"
            _LOGGER.error(error)
            raise IntegrationError(error)
            
        _LOGGER.debug(f"DLX response: {response}")
        return response

class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""