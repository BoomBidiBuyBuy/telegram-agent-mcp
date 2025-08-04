# telegram-agent-mcp

This repo implements proxy server that allows to access LLM Agent integrated with MCP tools


## Development

### Envs

Setup `.env` file from the `.env.example`

You can use `mysql` for the `STORAGE_DB`.

> [!IMPORTANT]
> Use `mysql` only for development since it keeps all data in memory  

### Setup

The following command will install necessary python pacakges
```
uv sync --dev
```

Then you need to configure `.env` file.
We distribute `.env.example`, copy it and fill with values you need
```
cp .env.example .env`
```

### Configuration

We support two way of communication bot with the telegram server:
- **polling**, ie when bot time to time go to the telegram servers and checks for new messages or events
- **webhook**, ie when the bot register it's own url where the telegram server should send new messages and events

The `COMMUNICATION_MODE` env variable handles it. The **polling** id default.


#### Webhook configuration

First of all set the `COMMUNICATION_MODE` to `webhook`.

Using webhook requires setting up SSL.

This command generates `private.key` and `cert.pem` files for SSL.
```
openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem
```
(use domain name / IP address when it asks for FQDN)

Then we need to define `SSL_KEY_PATH` and `SSL_CERT_PATH` env in `.env` to generated files.

The `WEBHOOK_PORT` should be set to 80, 88, 443 or 8443.

The `WEBHOOK_URL` needs to have format `https://<your-domain-or-ip>:<webhook-port>`. Port is required in the URL in this case.


### Run

```
uv run --env-file .env src/main
```

### Tests

```
uv run pytest -vs
```

### Linters

```
uv run ruff check
```

and 

```
uv run ruff format
```

for formatting


## Deployment

### Heroku

Heroku integrates only with the webhook mode.

You need to setup only the following envs on Heroku site:
- `COMMUNICATION_MODE=webhook`
- `WEBHOOK_URL=https://<your-app-id>.herokuapp.com/` (note that port should not be in the url because Heroku communicates application through a proxy)
- `TELEGRAM_BOT_TOKEN`

No need to setup `WEBHOOK_PORT`, `SSL_KEY_PATH` and `SSL_CERT_PATH` because Heroku manages SSL on their proxy side. As for the port, they assigned it through the `PORT` env variable that we use instead of `WEBHOOK_PORT` to be integrated with their approach.
