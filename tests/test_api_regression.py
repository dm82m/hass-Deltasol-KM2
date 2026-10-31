"""Regression tests for decoding DeltaSol VBus API date fields."""

import ast
import datetime
import logging
import unittest
from collections import namedtuple
from pathlib import Path

API_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "deltasol"
    / "deltasolapi.py"
)

DeltasolEndpoint = namedtuple(
    "DeltasolEndpoint",
    "name, value, unit, description, bus_dest, bus_src, product_details",
)


def load_api_parser():
    """Execute the actual production parser, without HA or requests imports."""
    tree = ast.parse(API_SOURCE.read_text(encoding="utf-8"))
    api = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DeltasolApi"
    )
    api.bases = []
    api.keywords = []
    api.body = [
        node
        for node in api.body
        if isinstance(node, ast.FunctionDef) and node.name == "__parse_data"
    ]
    namespace = {
        "datetime": datetime,
        "DeltasolEndpoint": DeltasolEndpoint,
        "_LOGGER": logging.getLogger(__name__),
    }
    # Only the parser from our checked-in production module is executed.
    exec(  # noqa: S102
        compile(
            ast.fix_missing_locations(ast.Module(body=[api], type_ignores=[])),
            str(API_SOURCE),
            "exec",
        ),
        namespace,
    )
    parser = namespace["DeltasolApi"]()
    parser.product_details = {"serial": "test-device"}
    return parser


def make_payload(epoch_seconds):
    """Construct a minimal realistic Resol live VBus headerset."""
    return {
        "headers": [
            {
                "id": "00_6653_7112_10_0200",
                "description": "Controller",
                "destination_name": "DFA",
                "source_name": "DeltaSol",
                "fields": [
                    {
                        "id": "001_3_0",
                        "name": "System date",
                        "unit": "",
                    },
                    {
                        "id": "004_2_0",
                        "name": "Collector temperature",
                        "unit": " °C ",
                    },
                    {
                        "id": "006_1_0",
                        "name": "Pump active",
                        "unit": "",
                    },
                ],
            }
        ],
        "headersets": [
            {
                "packets": [
                    {
                        "field_values": [
                            {"raw_value": epoch_seconds},
                            {"raw_value": 21.235},
                            {"raw_value": 0},
                        ]
                    }
                ]
            }
        ],
    }


class DeltasolDateParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = load_api_parser()

    def test_date_epoch_uses_real_utc_timezone(self):
        data = self.parser._DeltasolApi__parse_data(make_payload(0))
        value = data["00_6653_7112_10_0200__001_3_0"].value
        self.assertEqual(value, datetime.datetime(2001, 1, 1, tzinfo=datetime.UTC))
        self.assertEqual(value.utcoffset(), datetime.timedelta(0))

    def test_date_offset_and_other_sensor_values(self):
        data = self.parser._DeltasolApi__parse_data(make_payload(3661))
        self.assertEqual(
            data["00_6653_7112_10_0200__001_3_0"].value,
            datetime.datetime(2001, 1, 1, 1, 1, 1, tzinfo=datetime.UTC),
        )
        temperature = data["00_6653_7112_10_0200__004_2_0"]
        self.assertEqual(temperature.value, 21.23)
        self.assertEqual(temperature.unit, "°C")
        self.assertEqual(temperature.name, "collector_temperature")
        self.assertEqual(temperature.product_details["serial"], "test-device")
        self.assertEqual(data["00_6653_7112_10_0200__006_1_0"].value, 0)


if __name__ == "__main__":
    unittest.main()
