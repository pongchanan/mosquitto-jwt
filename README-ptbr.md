<h1 align="center" style="font-weight: bold;">Mosquitto MQTT Broker com Autenticação JWT</h1>

<div align="center">
  
![icon](https://github.com/Lima-e-Silva/mosquitto-jwt/blob/a144d184637be552fa8a73c566d88642954e2590/static/icon.png)

</div>

<div align="center">

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/mosquitto-broker-with-jwt-auth?referralCode=ePU7HL&utm_medium=integration&utm_source=template&utm_campaign=generic)

</div>

[Access the English version here](README.md)

<h2 id="info">📝 Informações</h2>

Este projeto fornece uma configuração para o broker MQTT Mosquitto com autenticação e autorização usando JSON Web Tokens (JWT). Ele utiliza o plugin [mosquitto-jwt-auth](https://github.com/wiomoc/mosquitto-jwt-auth) para gerenciar o acesso de clientes, permitindo controle robusto e flexível.

Saiba mais sobre o Mosquitto aqui: [Eclipse Mosquitto](https://mosquitto.org)

A solução é empacotada em um contêiner Docker, facilitando a implantação e o gerenciamento.

Se você acha que a Autenticação JWT é exagero, pode conferir esta implementação mais simples usando apenas autenticação USUÁRIO:SENHA: [mosquitto-railway-template](https://github.com/Lima-e-Silva/mosquitto-railway-template)

<h2 id="feat">✨ Recursos</h2>

- **Autenticação e Autorização JWT**: Usa JWTs para autenticar clientes MQTT e autorizar a publicação/inscrição em tópicos específicos.
- **Suporte a MQTT e WebSockets**: O broker é configurado para aceitar conexões MQTT padrão na porta `1883` e conexões MQTT via WebSockets na porta `9001`.
- **Fácil Implantação com Docker**: O `Dockerfile` automatiza a compilação do Mosquitto e do plugin JWT, criando uma imagem leve e pronta para uso.
- **Fácil Implantação no Railway**: Confira o template fornecido no Railway

## Sobre o JWT

Os clientes MQTT precisam de um JWT válido para se conectar. O token deve ser assinado com o `JWT_SECRET` configurado no broker.

Um JWT típico para esta configuração pode ter as seguintes reivindicações (claims):

```json
{
  "subs": ["topic/to/subscribe", "another/topic"],
  "publ": ["topic/to/publish", "yet/another/topic"]
}
```

- `subs`: Array de tópicos que o cliente tem permissão para se inscrever.
- `publ`: Array de tópicos que o cliente tem permissão para publicar.

Você pode usar ferramentas online (como [jwt.io](https://jwt.io/)) ou bibliotecas de programação para gerar esses tokens.

<h2 id="env">🔐 Variáveis</h2>

- `JWT_SECRET`: Chave secreta para autenticação JWT
- `MAX_CONNECTIONS`: O número máximo de conexões de clientes permitidas
- `MAX_QUEUED_MESSAGES`: O número máximo de mensagens QoS 1 ou 2 para manter na fila (por cliente)
- `MAX_INFLIGHT_MESSAGES`: O número máximo de mensagens QoS 1 ou 2 de saída que podem estar em processo de transmissão simultaneamente

<h2>🛠️ Exemplos</h2>

- [Como Publicar (Python)](https://github.com/Lima-e-Silva/mosquitto-jwt/wiki/How-to-Publish)
- [Como se Inscrever (Python)](https://github.com/Lima-e-Silva/mosquitto-jwt/wiki/How-to-Subscribe)
