<h1 align="center" style="font-weight: bold;">Mosquitto MQTT Broker with JWT Authentication</h1>

<div align="center">
  
![icon](https://github.com/Lima-e-Silva/mosquitto-jwt/blob/a144d184637be552fa8a73c566d88642954e2590/static/icon.png)

</div>

<div align="center">

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/mosquitto-broker-with-jwt-auth?referralCode=ePU7HL&utm_medium=integration&utm_source=template&utm_campaign=generic)

</div>

[Acesse a versão em Português aqui](README-ptbr.md)

<h2 id="info">📝 Info</h2>

This project provides a configuration for the Mosquitto MQTT broker with JSON Web Tokens (JWT) authentication and authorization. It uses the [mosquitto-jwt-auth](https://github.com/wiomoc/mosquitto-jwt-auth) plugin to manage client access, allowing for robust and flexible control.

Learn more about Mosquitto here: [Eclipse Mosquitto](https://mosquitto.org)

The solution is packaged in a Docker container, facilitating deployment and management.

If you think JWT Auth is overkill, you can check this simpler implementation using only USER:PASSWORD authentication: [mosquitto-railway-template](https://github.com/Lima-e-Silva/mosquitto-railway-template)

<h2 id="env">✨ Features</h2>

- **JWT Authentication & Authorization**: Uses JWTs to authenticate MQTT clients and authorize to pub/sub to specific topics.
- **MQTT and WebSockets Support**: The broker is configured to accept standard MQTT connections on port `1883` and MQTT over WebSockets connections on port `9001`.
- **Easy Deployment with Docker**: The `Dockerfile` automates the compilation of Mosquitto and the JWT plugin, creating a lightweight and ready-to-use image.
- **Easy Deployment on Railway**: Check the template provided in Railway

## About the JWT

MQTT clients need a valid JWT to connect. The token must be signed with the `JWT_SECRET` configured in the broker.

A typical JWT for this setup might have the following claims:

```json
{
  "subs": ["topic/to/subscribe", "another/topic"],
  "publ": ["topic/to/publish", "yet/another/topic"]
}
```

- `subs`: Array of topics the client is allowed to subscribe to.
- `publ`: Array of topics the client is allowed to publish to.

You can use online tools (like [jwt.io](https://jwt.io/)) or programming libraries to generate these tokens.

<h2 id="env">🔐 Variables</h2>

- `JWT_SECRET`: Secret key for JWT authentication
- `MAX_CONNECTIONS`: The maximum number of client connections allowed
- `MAX_QUEUED_MESSAGES`: The maximum number of QoS 1 or 2 messages to hold in the queue (per client)
- `MAX_INFLIGHT_MESSAGES`: The maximum number of outgoing QoS 1 or 2 messages that can be in the process of being transmitted simultaneously

<h2>🛠️ Examples</h2>

- [How to Publish (Python)](https://github.com/Lima-e-Silva/mosquitto-jwt/wiki/How-to-Publish)
- [How to Subscribe (Python)](https://github.com/Lima-e-Silva/mosquitto-jwt/wiki/How-to-Subscribe)
