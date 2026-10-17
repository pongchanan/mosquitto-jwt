"""
Test suite for Mosquitto MQTT Broker with JWT Authentication
Tests both TCP and WebSocket connections
"""

import os
import ssl
import time

import jwt
import paho.mqtt.client as mqtt
import pytest
from dotenv import load_dotenv

load_dotenv()

MOSQUITTO_TCP_HOST = os.getenv("MOSQUITTO_TCP_HOST", "localhost")
MOSQUITTO_TCP_PORT = int(os.getenv("MOSQUITTO_TCP_PORT", "1883"))
MOSQUITTO_WS_HOST = os.getenv("MOSQUITTO_WS_HOST", "localhost")
MOSQUITTO_WS_PORT = int(os.getenv("MOSQUITTO_WS_PORT", "9001"))
MOSQUITTO_USER = os.getenv("MOSQUITTO_USER", "admin")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")

TEST_TOPIC = "test/broker"
TEST_MESSAGE = "Test message from pytest suite"
TIMEOUT = 10  # seconds

payload = {
    "subs": [TEST_TOPIC, "test/#", "restrict/#"],
    "publ": [TEST_TOPIC, "test/#"],
}
MOSQUITTO_PASSWORD = jwt.encode(payload=payload, key=JWT_SECRET, algorithm="HS256")


class TestMessageReceiver:
    """Helper class to receive MQTT messages"""

    def __init__(self):
        self.messages = []
        self.connected = False
        self.error = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
        else:
            self.error = f"Connection failed with code {rc}"

    def on_message(self, client, userdata, msg):
        self.messages.append(
            {"topic": msg.topic, "payload": msg.payload.decode(), "qos": msg.qos}
        )


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# MARK: TCP
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_tcp_publish():
    """Test publishing a message via TCP connection"""
    client = mqtt.Client()
    client.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    try:
        client.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)
        response = client.publish(TEST_TOPIC, TEST_MESSAGE, qos=0)

        assert response.rc == 0, f"Failed to publish message: {response.rc}"
    except Exception as e:
        pytest.fail(f"TCP Publish failed: {str(e)}")
    finally:
        client.disconnect()


def test_tcp_subscribe_and_receive():
    """Test subscribing and receiving a message via TCP connection"""
    receiver = TestMessageReceiver()
    client = mqtt.Client()
    client.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    client.on_connect = receiver.on_connect
    client.on_message = receiver.on_message

    try:
        # Connect and subscribe
        client.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)
        client.subscribe(TEST_TOPIC, qos=0)
        client.loop_start()

        # Wait for connection
        start_time = time.time()
        while not receiver.connected and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        assert receiver.connected, "Failed to connect via TCP"

        # Publish a test message (using a separate client)
        publisher = mqtt.Client()
        publisher.username_pw_set(
            username=MOSQUITTO_USER,
            password=MOSQUITTO_PASSWORD,
        )
        publisher.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)
        publisher.publish(TEST_TOPIC, TEST_MESSAGE, qos=0)
        publisher.disconnect()

        # Wait for message reception
        start_time = time.time()
        while len(receiver.messages) == 0 and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        client.loop_stop()
        client.disconnect()

        assert len(receiver.messages) > 0, "No message received via TCP"
        assert receiver.messages[0]["topic"] == TEST_TOPIC
        assert receiver.messages[0]["payload"] == TEST_MESSAGE

    except Exception as e:
        client.loop_stop()
        client.disconnect()
        pytest.fail(f"TCP Subscribe failed: {str(e)}")


def test_unauthorized_publish_tcp():
    """
    Test that an authenticated user WITHOUT publish authorization to a topic
    cannot successfully publish to that topic.

    The user is authenticated (valid JWT) but not authorized to publish to the restricted topic.
    The subscriber with proper authorization should NOT receive the message.
    """
    # Topic that unauthorized user will try to publish to
    RESTRICTED_TOPIC = "restrict/topic"

    # Create a subscriber WITH authorization to the restricted topic
    receiver = TestMessageReceiver()
    subscriber = mqtt.Client()

    # Subscriber has full permissions
    subscriber.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )
    subscriber.on_connect = receiver.on_connect
    subscriber.on_message = receiver.on_message

    # Create an unauthorized publisher (authenticated but no publish permission)
    publisher = mqtt.Client()
    publisher.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    try:
        # Connect subscriber to RESTRICTED_TOPIC (has authorization)
        subscriber.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)
        subscriber.subscribe(RESTRICTED_TOPIC, qos=0)
        subscriber.loop_start()

        # Wait for subscriber connection
        start_time = time.time()
        while not receiver.connected and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        assert receiver.connected, "Subscriber failed to connect"

        # Unauthorized publisher tries to publish to RESTRICTED_TOPIC
        publisher.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)

        # Note: The publish call may succeed (rc=0) from the client perspective,
        # but the broker should reject the message due to lack of authorization
        publisher.publish(RESTRICTED_TOPIC, TEST_MESSAGE, qos=0)
        publisher.disconnect()

        # Wait to ensure no message arrives
        time.sleep(2)

        subscriber.loop_stop()
        subscriber.disconnect()

        # The subscriber should NOT receive any message
        assert len(receiver.messages) == 0, (
            "Subscriber received message from unauthorized publisher - authorization failed!"
        )

    except Exception as e:
        subscriber.loop_stop()
        subscriber.disconnect()
        publisher.disconnect()
        pytest.fail(f"Unauthorized publish test failed: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# MARK: WS
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_websocket_publish():
    """Test publishing a message via WebSocket connection"""
    client = mqtt.Client(transport="websockets")
    client.ws_set_options(path="/", headers=None)
    client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    try:
        client.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)
        response = client.publish(TEST_TOPIC, TEST_MESSAGE, qos=0)

        assert response.rc == 0, f"Failed to publish message via WS: {response.rc}"
    except Exception as e:
        pytest.fail(f"WebSocket Publish failed: {str(e)}")
    finally:
        client.disconnect()


def test_websocket_subscribe_and_receive():
    """Test subscribing and receiving a message via WebSocket connection"""
    receiver = TestMessageReceiver()
    client = mqtt.Client(transport="websockets")
    client.ws_set_options(path="/", headers=None)
    client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    client.on_connect = receiver.on_connect
    client.on_message = receiver.on_message

    try:
        # Connect and subscribe
        client.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)
        client.subscribe(TEST_TOPIC, qos=0)
        client.loop_start()

        # Wait for connection
        start_time = time.time()
        while not receiver.connected and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        assert receiver.connected, "Failed to connect via WebSocket"

        # Publish a test message (using a separate WS client)
        publisher = mqtt.Client(transport="websockets")
        publisher.ws_set_options(path="/", headers=None)
        publisher.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
        publisher.username_pw_set(
            username=MOSQUITTO_USER,
            password=MOSQUITTO_PASSWORD,
        )
        publisher.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)
        publisher.publish(TEST_TOPIC, TEST_MESSAGE, qos=0)
        publisher.disconnect()

        # Wait for message reception
        start_time = time.time()
        while len(receiver.messages) == 0 and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        client.loop_stop()
        client.disconnect()

        assert len(receiver.messages) > 0, "No message received via WebSocket"
        assert receiver.messages[0]["topic"] == TEST_TOPIC
        assert receiver.messages[0]["payload"] == TEST_MESSAGE

    except Exception as e:
        client.loop_stop()
        client.disconnect()
        pytest.fail(f"WebSocket Subscribe failed: {str(e)}")


def test_unauthorized_publish_websocket():
    """
    Test that an authenticated user WITHOUT publish authorization to a topic
    cannot successfully publish to that topic via WebSocket.

    The user is authenticated (valid JWT) but not authorized to publish to the restricted topic.
    The subscriber with proper authorization should NOT receive the message.
    """
    # Topic that unauthorized user will try to publish to
    RESTRICTED_TOPIC = "restricted/topic"

    # Create a subscriber WITH authorization to the restricted topic
    receiver = TestMessageReceiver()
    subscriber = mqtt.Client(transport="websockets")
    subscriber.ws_set_options(path="/", headers=None)
    subscriber.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Subscriber has full permissions
    subscriber.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )
    subscriber.on_connect = receiver.on_connect
    subscriber.on_message = receiver.on_message

    # Create an unauthorized publisher (authenticated but no publish permission)
    publisher = mqtt.Client(transport="websockets")
    publisher.ws_set_options(path="/", headers=None)
    publisher.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
    publisher.username_pw_set(
        username=MOSQUITTO_USER,
        password=MOSQUITTO_PASSWORD,
    )

    try:
        # Connect subscriber to RESTRICTED_TOPIC (has authorization)
        subscriber.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)
        subscriber.subscribe(RESTRICTED_TOPIC, qos=0)
        subscriber.loop_start()

        # Wait for subscriber connection
        start_time = time.time()
        while not receiver.connected and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        assert receiver.connected, "Subscriber failed to connect via WebSocket"

        # Unauthorized publisher tries to publish to RESTRICTED_TOPIC
        publisher.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)

        # Note: The publish call may succeed (rc=0) from the client perspective,
        # but the broker should reject the message due to lack of authorization
        publisher.publish(RESTRICTED_TOPIC, TEST_MESSAGE, qos=0)
        publisher.disconnect()

        # Wait to ensure no message arrives
        time.sleep(2)

        subscriber.loop_stop()
        subscriber.disconnect()

        # The subscriber should NOT receive any message
        assert len(receiver.messages) == 0, (
            "Subscriber received message from unauthorized publisher - authorization failed!"
        )

    except Exception as e:
        subscriber.loop_stop()
        subscriber.disconnect()
        publisher.disconnect()
        pytest.fail(f"Unauthorized publish test failed: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# MARK: CROSS PROTOCOL
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_cross_protocol_communication():
    """Test that messages published via TCP can be received via WebSocket"""
    receiver = TestMessageReceiver()

    # Create WebSocket subscriber
    ws_client = mqtt.Client(transport="websockets")
    ws_client.ws_set_options(path="/", headers=None)
    ws_client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
    ws_client.username_pw_set(username=MOSQUITTO_USER, password=MOSQUITTO_PASSWORD)
    ws_client.on_connect = receiver.on_connect
    ws_client.on_message = receiver.on_message

    try:
        # Connect WebSocket subscriber
        ws_client.connect(MOSQUITTO_WS_HOST, MOSQUITTO_WS_PORT, keepalive=60)
        ws_client.subscribe(TEST_TOPIC, qos=0)
        ws_client.loop_start()

        # Wait for WebSocket connection
        start_time = time.time()
        while not receiver.connected and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        assert receiver.connected, "WebSocket subscriber failed to connect"

        # Publish via TCP
        tcp_client = mqtt.Client()
        tcp_client.username_pw_set(username=MOSQUITTO_USER, password=MOSQUITTO_PASSWORD)
        tcp_client.connect(MOSQUITTO_TCP_HOST, MOSQUITTO_TCP_PORT, keepalive=60)
        tcp_client.publish(TEST_TOPIC, TEST_MESSAGE, qos=0)
        tcp_client.disconnect()

        # Wait for message reception via WebSocket
        start_time = time.time()
        while len(receiver.messages) == 0 and time.time() - start_time < TIMEOUT:
            time.sleep(0.1)

        ws_client.loop_stop()
        ws_client.disconnect()

        assert len(receiver.messages) > 0, (
            "Message not received via WebSocket from TCP publisher"
        )
        assert receiver.messages[0]["payload"] == TEST_MESSAGE

    except Exception as e:
        ws_client.loop_stop()
        ws_client.disconnect()
        pytest.fail(f"Cross-protocol test failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
