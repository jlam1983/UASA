"""Stream data channel adapter."""

from __future__ import annotations

import json
from typing import Generator, Any
from dataclasses import dataclass

from ..exceptions import ChannelReadError


@dataclass
class StreamMessage:
    topic: str
    data: dict | list
    timestamp: float
    offset: int | None = None
    partition: int | None = None
    key: str | None = None


class StreamChannel:
    """Handles streaming data sources (Kafka, Kinesis, WebSocket, SSE, RabbitMQ)."""

    def __init__(self, bootstrap_servers: list[str] | None = None, consumer_group: str | None = None):
        self.bootstrap_servers = bootstrap_servers or []
        self.consumer_group = consumer_group
        self._consumer = None
        self._ws = None

    def connect_kafka(self, topic: str, **kwargs) -> None:
        """Connect to Kafka topic."""
        try:
            from kafka import KafkaConsumer
            self._consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                **kwargs,
            )
        except ImportError:
            raise ChannelReadError("kafka-python not installed. Run: pip install kafka-python")

    def connect_kinesis(self, stream_name: str, region: str = "us-east-1") -> None:
        """Connect to AWS Kinesis stream."""
        try:
            import boto3
            self._kinesis = boto3.client("kinesis", region_name=region)
            self._stream_name = stream_name
        except ImportError:
            raise ChannelReadError("boto3 not installed. Run: pip install boto3")

    def connect_websocket(self, url: str, headers: dict | None = None) -> None:
        """Connect to WebSocket endpoint."""
        try:
            import websocket
            self._ws_url = url
            self._ws_headers = headers or {}
            self._ws = websocket.WebSocket()
            self._ws.connect(url, header=headers)
        except ImportError:
            raise ChannelReadError("websocket-client not installed. Run: pip install websocket-client")

    def connect_sse(self, url: str, headers: dict | None = None) -> None:
        """Connect to Server-Sent Events endpoint."""
        import urllib.request
        self._sse_url = url
        self._sse_headers = headers or {}

    def connect_rabbitmq(self, queue: str, host: str = "localhost", **kwargs) -> None:
        """Connect to RabbitMQ queue."""
        try:
            import pika
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, **kwargs))
            channel = connection.channel()
            channel.queue_declare(queue=queue)
            self._rabbit_connection = connection
            self._rabbit_channel = channel
            self._rabbit_queue = queue
        except ImportError:
            raise ChannelReadError("pika not installed. Run: pip install pika")

    def consume(self, topic: str, **kwargs) -> Generator[dict, None, None]:
        """Consume messages from stream."""
        if self._consumer is not None:
            for message in self._consumer:
                yield message.value
        elif hasattr(self, "_kinesis"):
            shard_id = kwargs.get("shard_id")
            if shard_id is None:
                raise ChannelReadError("shard_id required for Kinesis")
            response = self._kinesis.get_shard_iterator(
                StreamName=self._stream_name,
                ShardId=shard_id,
                ShardIteratorType="LATEST",
            )
            shard_iter = response["ShardIterator"]
            while True:
                response = self._kinesis.get_records(
                    ShardIterator=shard_iter,
                    Limit=10,
                )
                for record in response["Records"]:
                    yield json.loads(record["Data"])
                shard_iter = response["NextShardIterator"]
        elif self._ws is not None:
            while True:
                data = self._ws.recv()
                yield json.loads(data)
        elif hasattr(self, "_sse_url"):
            import urllib.request
            request = urllib.request.Request(self._sse_url, headers=self._sse_headers)
            with urllib.request.urlopen(request) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data:"):
                        yield json.loads(line[5:].strip())
        elif hasattr(self, "_rabbit_channel"):
            import pika
            for method_frame, properties, body in self._rabbit_channel.consume(
                queue=self._rabbit_queue, inactivity_timeout=1
            ):
                if body:
                    yield json.loads(body)
                if method_frame is None:
                    break
        else:
            raise ChannelReadError("No stream connection established. Call connect_* method first.")

    def acknowledge(self, message_id: str) -> None:
        """Acknowledge message processing."""
        pass

    def close(self) -> None:
        """Close all connections."""
        if self._consumer:
            self._consumer.close()
        if self._ws:
            self._ws.close()
        if hasattr(self, "_rabbit_connection"):
            self._rabbit_connection.close()
