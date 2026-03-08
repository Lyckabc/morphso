# Infisical SDK usage (Morphso)

Morphso exposes Infisical operations at `/api/v1/secret/...`. Configure the container with these env vars (do not hardcode; use `${INFISICAL_PATH/...}` or secrets injection).

## SDK / API env

| Variable | Purpose |
|----------|---------|
| `INFISICAL_HOST` | Infisical server URL (e.g. `https://infisical.toji.homes` or `https://app.infisical.com`) |
| `INFISICAL_TOKEN` | Access token for all API calls |
| `INFISICAL_CLIENT_ID` | Machine identity client ID (alternative to token) |
| `INFISICAL_CLIENT_SECRET` | Machine identity client secret (use with `INFISICAL_CLIENT_ID`) |
| `INFISICAL_PROJECT_ID` | Default project for secrets/folders (optional) |
| `INFISICAL_ENVIRONMENT_SLUG` | Default environment, e.g. `dev` (optional, default `dev`) |
| `INFISICAL_SECRET_PATH` | Default secret path (optional, default `/`) |

Use either `INFISICAL_TOKEN` or `INFISICAL_CLIENT_ID` + `INFISICAL_CLIENT_SECRET`. If none are set, `/api/v1/secret/*` endpoints return 503.

## Docker run example

```bash
docker run -d --name morphso -p 8013:8013 \
  -e INFISICAL_HOST=https://infisical.toji.homes \
  -e "INFISICAL_TOKEN=${INFISICAL_TOKEN}" \
  -e "INFISICAL_PROJECT_ID=${INFISICAL_PROJECT_ID}" \
  -e DB_ADMIN_USER=postgres \
  -e "DB_ADMIN_PASSWORD=${DB_ADMIN_PASSWORD}" \
  -e DB_ADMIN_HOST=postgres_db \
  registry.toji.homes/morphso:latest
```

## Test: secret create and list

Organization **neunexus** (`organization_id`: `822f8bc9-f076-4a39-b164-bd20248cb1b4`). Use a **project** under this org: get **Project ID** from Infisical Dashboard → your project → Project Settings.

1. Set in `.env` (do not commit secrets):
   - `INFISICAL_HOST=https://infisical.toji.homes`
   - `INFISICAL_TOKEN=<machine-identity or user token from Infisical>`
   - `INFISICAL_PROJECT_ID=<project-id from Project Settings>`

2. Start Morphso (local or Docker):
   ```bash
   source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8013
   ```
   Or with Docker: use the run example above with the same env vars.

3. Run the test script (creates POSTGRES_* secrets and lists/gets them):
   ```bash
   export INFISICAL_PROJECT_ID=<same project id>
   python scripts/test_infisical_secrets.py
   ```

The script creates these secrets in the project (path `/`, environment `dev`): `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DNS_HOST`, then lists all secrets and gets `POSTGRES_USER` and `POSTGRES_DB` by name.
