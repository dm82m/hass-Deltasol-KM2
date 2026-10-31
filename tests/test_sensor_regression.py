"""Dependency-free regression tests for DeltaSol sensor coordinator updates.

Execute the production sensor property implementations in isolation so tests
do not require a running Home Assistant instance.
"""

import ast
import logging
import unittest
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

SENSOR_SOURCE = (
    Path(__file__).resolve().parents[1] / "custom_components" / "deltasol" / "sensor.py"
)
INITIAL_TIME = datetime(2026, 1, 1, tzinfo=UTC)
UPDATE_TIME = datetime(2026, 1, 2, tzinfo=UTC)


class SensorDeviceClass:
    TEMPERATURE = "temperature"
    POWER_FACTOR = "power_factor"
    ENERGY = "energy"
    POWER = "power"
    DATE = "date"


def load_sensor_properties():
    """Load the actual production methods without HA import dependencies."""
    tree = ast.parse(SENSOR_SOURCE.read_text(encoding="utf-8"))
    entity = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DeltasolSensor"
    )
    methods = {
        "available",
        "_handle_coordinator_update",
        "native_value",
        "device_class",
    }
    entity.bases = []
    entity.keywords = []
    entity.body = [
        node
        for node in entity.body
        if isinstance(node, ast.FunctionDef) and node.name in methods
    ]
    # The HA @callback decorator is an identity decorator for these tests.
    namespace = {
        "callback": lambda function: function,
        "date": date,
        "dt_util": SimpleNamespace(now=lambda: UPDATE_TIME),
        "_LOGGER": logging.getLogger(__name__),
        "SensorDeviceClass": SensorDeviceClass,
        "UnitOfTemperature": SimpleNamespace(CELSIUS="°C"),
        "UnitOfEnergy": SimpleNamespace(WATT_HOUR="Wh"),
        "UnitOfPower": SimpleNamespace(WATT="W"),
        "PERCENTAGE": "%",
    }
    # Only our checked-in sensor.py methods are executed in this test harness.
    exec(  # noqa: S102
        compile(
            ast.fix_missing_locations(ast.Module(body=[entity], type_ignores=[])),
            str(SENSOR_SOURCE),
            "exec",
        ),
        namespace,
    )
    return namespace["DeltasolSensor"]


class DeltasolSensorRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sensor_type = load_sensor_properties()

    def make_sensor(self, data, *, success=True, initial_value=14, unit=""):
        sensor = self.sensor_type()
        sensor.unique_id = "vbus-field-1"
        sensor.name = "test_sensor"
        sensor.coordinator = SimpleNamespace(
            last_update_success=success,
            data=data,
        )
        sensor._endpoint = SimpleNamespace(value=initial_value)
        sensor._unit = unit
        sensor._last_updated = INITIAL_TIME
        sensor.state_writes = []
        sensor.async_write_ha_state = lambda: sensor.state_writes.append(True)
        return sensor

    def test_missing_field_is_unavailable_without_exception(self):
        sensor = self.make_sensor({})
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)
        self.assertIsNone(sensor.device_class)

    def test_zero_false_and_empty_string_are_not_synthesized(self):
        for value in (0, False, ""):
            with self.subTest(value=value):
                sensor = self.make_sensor(
                    {"vbus-field-1": SimpleNamespace(value=value)}
                )
                self.assertTrue(sensor.available)
                self.assertEqual(sensor.native_value, value)
                self.assertEqual(type(sensor.native_value), type(value))

    def test_missing_update_preserves_last_seen_and_recovers(self):
        sensor = self.make_sensor({})
        sensor._handle_coordinator_update()
        self.assertEqual(sensor._last_updated, INITIAL_TIME)
        self.assertEqual(len(sensor.state_writes), 1)
        sensor.coordinator.data = {"vbus-field-1": SimpleNamespace(value=22.5)}
        sensor._handle_coordinator_update()
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.native_value, 22.5)
        self.assertEqual(sensor._last_updated, UPDATE_TIME)
        self.assertEqual(len(sensor.state_writes), 2)

    def test_failed_poll_does_not_expose_cached_value(self):
        sensor = self.make_sensor(
            {"vbus-field-1": SimpleNamespace(value=7)}, success=False
        )
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)
        sensor._handle_coordinator_update()
        self.assertEqual(sensor._last_updated, INITIAL_TIME)

    def test_date_class_is_stable_while_field_missing(self):
        sensor = self.make_sensor({}, initial_value=date(2026, 1, 1))
        self.assertFalse(sensor.available)
        self.assertEqual(sensor.device_class, SensorDeviceClass.DATE)

    def test_temperature_class_is_stable_while_field_missing(self):
        sensor = self.make_sensor({}, initial_value=20, unit="°C")
        self.assertEqual(sensor.device_class, SensorDeviceClass.TEMPERATURE)

    def test_none_data_is_handled(self):
        sensor = self.make_sensor(None)
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)


if __name__ == "__main__":
    unittest.main()
