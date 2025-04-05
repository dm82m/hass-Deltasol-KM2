"""
Gets sensor data from Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB using api.
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2
"""

import datetime
import logging
import re
from collections import namedtuple

import requests
from homeassistant.exceptions import IntegrationError
from requests.exceptions import RequestException

_LOGGER = logging.getLogger(__name__)

DeltasolEndpoint = namedtuple(
    "DeltasolEndpoint",
    "name, value, unit, description, bus_dest, bus_src, product_details",
)


class DeltasolApi:
    """Wrapper class for Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB."""

    def __init__(self, host, port, username=None, password=None, api_key=None) -> None:
        """Initialise api."""
        self.data = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.api_key = api_key
        self.product = None
        self.product_details = None

    def __parse_data(self, response) -> dict[str, DeltasolEndpoint]:
        data = {}

        iHeader = 0
        for header in response["headers"]:
            _LOGGER.debug(f"Found header[{iHeader}] now parsing it ...")
            iField = 0
            for field in response["headers"][iHeader]["fields"]:
                value = response["headersets"][0]["packets"][iHeader]["field_values"][
                    iField
                ]["raw_value"]
                if isinstance(value, float):
                    value = round(value, 2)
                if "date" in field["name"]:
                    epochStart = datetime.datetime(2001, 1, 1, 0, 0, 0, 0)
                    value = epochStart + datetime.timedelta(0, value)
                unique_id = header["id"] + "__" + field["id"]
                data[unique_id] = DeltasolEndpoint(
                    name=field["name"].replace(" ", "_").lower(),
                    value=value,
                    unit=field["unit"].strip(),
                    description=header["description"],
                    bus_dest=header["destination_name"],
                    bus_src=header["source_name"],
                    product_details=self.product_details,
                )
                iField += 1
            iHeader += 1

        return data

    def detect_product(self):
        if self.product is not None:
            return self.product

        try:
            url = f"http://{self.host}:{self.port}/cgi-bin/get_resol_device_information"
            _LOGGER.info(f"Auto detecting Resol product from {url}")
            response = requests.request("GET", url)
            if response.status_code == 200:
                _LOGGER.debug(f"response: {response.text}")
                matches = re.search(r'product\s=\s["](.*?)["]', response.text)
                if matches:
                    self.product = matches.group(1).lower()
                    _LOGGER.info(f"Detected Resol product: {self.product}")
                    product_details = {
                        "vendor": re.search(
                            r'vendor\s=\s["](.*?)["]', response.text
                        ).group(1),
                        "serial": re.search(
                            r'serial\s=\s["](.*?)["]', response.text
                        ).group(1),
                        "version": re.search(
                            r'version\s=\s["](.*?)["]', response.text
                        ).group(1),
                        "build": re.search(
                            r'build\s=\s["](.*?)["]', response.text
                        ).group(1),
                        "name": re.search(r'name\s=\s["](.*?)["]', response.text).group(
                            1
                        ),
                        "features": re.search(
                            r'features\s=\s["](.*?)["]', response.text
                        ).group(1),
                        "mac": self.transform_to_mac(
                            re.search(r'serial\s=\s["](.*?)["]', response.text).group(1)
                        ),
                    }
                    self.product_details = product_details
                    _LOGGER.debug(f"Product Details: {product_details}")
                else:
                    error = "Your device was reachable but we could not correctly detect it, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
                    _LOGGER.error(error)
                    raise IntegrationError(error)
            else:
                error = "Are you sure you entered the correct address of the Resol KM2/DL2/DL2Plus/DL3 device? Please re-check and if the issue still persists, please file an issue here: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
                _LOGGER.error(error)
                raise IntegrationError(error)

        except RequestException as e:
            error = f"Error detecting Resol product - {e}, please file an issue at: https://github.com/dm82m/hass-Deltasol-KM2/issues/new/choose"
            _LOGGER.error(error)
            raise IntegrationError(error)

        return self.product

    def fetch_data(self) -> dict[str, DeltasolEndpoint] | None:
        """Use api to get data"""

        try:
            product = self.detect_product()

            response = {}
            if product == "km2" or product == "dl2plus":
                response = self.fetch_data_km2()
            elif product == "dl2" or product == "dl3":
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
            if not self.username or not self.password:
                raise KeyError()

            headers = {"Content-Type": "application/json"}

            payload = (
                "[{'id': '1','jsonrpc': '2.0','method': 'login','params': {'username': '"
                + self.username
                + "','password': '"
                + self.password
                + "'}}]"
            )
            response = requests.request(
                "POST", url, headers=headers, data=payload
            ).json()
            authId = response[0]["result"]["authId"]

            payload = (
                "[{'id': '1','jsonrpc': '2.0','method': 'dataGetCurrentData','params': {'authId': '"
                + authId
                + "'}}]"
            )
            response = requests.request(
                "POST", url, headers=headers, data=payload
            ).json()
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

        if self.username is not None and self.password is not None:
            auth = f"?sessionAuthUsername={self.username}&sessionAuthPassword={self.password}"
            filter = f"&filter={self.api_key}" if self.api_key else ""
            url = f"{url}{auth}{filter}"
            debugMessage = (
                f"DLX requesting sensor data url {url.replace(self.password, '***')}"
            )

        _LOGGER.debug(debugMessage)

        response = requests.request("GET", url)

        if response.status_code == 200:
            response = response.json()
        else:
            error = "Please re-check your username and password in your configuration!"
            _LOGGER.error(error)
            raise IntegrationError(error)

        _LOGGER.debug(f"DLX response: {response}")
        return response

    def transform_to_mac(self, serial: str) -> str:
        """Transform a string to MAC address format with ':' every 2 characters."""
        return ":".join(serial[i : i + 2] for i in range(0, len(serial), 2))
