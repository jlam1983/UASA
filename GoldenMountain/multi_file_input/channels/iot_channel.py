"""IoT cloud channel adapter.

Each channel has exactly 2 methods:
- read(device_ids) -> Generator[TelemetryData] (subscribe to devices)
- export(device_id, data) -> None (send to device)
"""

from __future__ import annotations

import json
from typing import Generator, Any
from dataclasses import dataclass

from ..exceptions import ChannelReadError


@dataclass
class TelemetryData:
    device_id: str
    timestamp: float
    data: dict
    quality: str = "good"


class IoTChannel:
    """Connects to IoT cloud platforms for reading telemetry and sending commands."""

    def __init__(self, platform: str | None = None, region: str | None = None):
        self.platform = platform
        self.region = region
        self._client = None
        self._mqtt_client = None

    def connect_aws_iot(
        self,
        endpoint: str,
        credentials: dict,
        cert_path: str | None = None,
        private_key_path: str | None = None,
    ) -> None:
        """Connect to AWS IoT Core."""
        try:
            import boto3
            from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

            self._iot = boto3.client("iot", region_name=self.region or "us-east-1")

            self._mqtt_client = AWSIoTMQTTClient("data-processor")
            self._mqtt_client.configureEndpoint(endpoint, 8883)
            if cert_path and private_key_path:
                self._mqtt_client.configureCredentials(cert_path, private_key_path)
            self._mqtt_client.connect()
        except ImportError:
            raise ChannelReadError("AWS IoT SDK not installed. Run: pip install AWSIoTPythonSDK boto3")

    def connect_azure_iot(
        self,
        connection_string: str,
        device_id: str,
    ) -> None:
        """Connect to Azure IoT Hub."""
        try:
            from azure.iot.device import IoTHubDeviceClient

            self._azure_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
            self._azure_client.connect()
            self._device_id = device_id
        except ImportError:
            raise ChannelReadError("Azure IoT SDK not installed. Run: pip install azure-iot-device")

    def connect_gcp_iot(
        self,
        project_id: str,
        registry_id: str,
        device_id: str,
        credentials_path: str | None = None,
    ) -> None:
        """Connect to Google Cloud IoT."""
        try:
            import google.cloud.iot_v1

            self._gcp_project = project_id
            self._gcp_registry = registry_id
            self._gcp_device = device_id
        except ImportError:
            raise ChannelReadError("Google Cloud IoT SDK not installed. Run: pip install google-cloud-iot")

    def connect_mqtt(
        self,
        broker_url: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        client_id: str = "data-processor",
    ) -> None:
        """Connect to MQTT broker."""
        try:
            import paho.mqtt.client as mqtt

            self._mqtt_client = mqtt.Client(client_id=client_id)
            if username and password:
                self._mqtt_client.username_pw_set(username, password)
            self._mqtt_client.connect(broker_url, port)
            self._mqtt_client.loop_start()
        except ImportError:
            raise ChannelReadError("paho-mqtt not installed. Run: pip install paho-mqtt")

    def read(self, device_ids: list[str]) -> Generator[TelemetryData, None, None]:
        """Subscribe to device telemetry.

        Args:
            device_ids: List of device IDs to subscribe to

        Returns:
            Generator of TelemetryData objects
        """
        if hasattr(self, "_mqtt_client") and self._mqtt_client:
            import paho.mqtt.client as mqtt

            telemetry_buffer = []

            def on_message(client, userdata, msg):
                try:
                    data = json.loads(msg.payload)
                    telemetry_buffer.append(data)
                except json.JSONDecodeError:
                    pass

            for device_id in device_ids:
                topic = f"devices/{device_id}/telemetry"
                self._mqtt_client.subscribe(topic)
                self._mqtt_client.on_message = on_message

            import time
            while telemetry_buffer:
                yield telemetry_buffer.pop(0)
                time.sleep(0.1)
        else:
            raise ChannelReadError("No MQTT client connected. Call connect_mqtt first.")

    def export(self, device_id: str, data: dict) -> None:
        """Export normalized JSON to IoT device.

        Args:
            device_id: Target device ID
            data: Normalized JSON dict (metadata + records)
        """
        if hasattr(self, "_mqtt_client") and self._mqtt_client:
            topic = f"devices/{device_id}/commands"
            payload = json.dumps(data)
            self._mqtt_client.publish(topic, payload)
        elif self.platform == "aws_iot" and hasattr(self, "_iot"):
            # AWS IoT shadow update
            payload = json.dumps({"state": {"desired": data}})
            self._iot.update_thing_shadow(thingName=device_id, payload=payload)
        elif self.platform == "azure_iot" and hasattr(self, "_azure_client"):
            self._azure_client.send_message(json.dumps(data))
        else:
            raise ChannelReadError(f"export not supported for platform: {self.platform}")

    def get_shadow(self, device_id: str) -> dict:
        """Get device shadow state."""
        if self.platform == "aws_iot" and hasattr(self, "_iot"):
            response = self._iot.get_thing_shadow(thingName=device_id)
            return json.loads(response["payload"].read().decode())
        elif self.platform == "azure_iot" and hasattr(self, "_azure_client"):
            twin = self._azure_client.get_twin()
            return twin
        else:
            raise ChannelReadError(f"get_shadow not supported for platform: {self.platform}")

    def update_shadow(self, device_id: str, desired_state: dict) -> None:
        """Update device shadow state."""
        if self.platform == "aws_iot" and hasattr(self, "_iot"):
            payload = json.dumps({"state": {"desired": desired_state}})
            self._iot.update_thing_shadow(thingName=device_id, payload=payload)
        elif self.platform == "azure_iot" and hasattr(self, "_azure_client"):
            self._azure_client.patch_twin({"properties": {"desired": desired_state}})
        else:
            raise ChannelReadError(f"update_shadow not supported for platform: {self.platform}")

    def close(self) -> None:
        """Close all connections."""
        if hasattr(self, "_mqtt_client") and self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        if hasattr(self, "_azure_client"):
            self._azure_client.disconnect()
