# Deployment

Production deploys are handled by GitHub Actions in `.github/workflows/deploy.yml`.

## Trigger

- Push or merge into `main`
- Manual run from GitHub Actions via `workflow_dispatch`

## Required GitHub Secrets

- `SERVER_HOST`: remote server hostname or IP
- `SERVER_USER`: SSH user
- `SERVER_SSH_KEY`: private SSH key allowed to log in as `SERVER_USER`

## Optional GitHub Variables

- `SERVER_APP_DIR`: repository path on the server. Defaults to `/opt/financial-dashboard`.
- `BACKEND_SERVICE_NAME`: systemd service restarted after deploy. Defaults to `financial-dashboard-backend`.

## Remote Server Assumptions

- The repository already exists at `SERVER_APP_DIR`.
- The SSH user can run `git fetch` and `git reset --hard origin/main` in that repository.
- Node.js/npm and Python 3 are installed on the server.
- The backend runs under a systemd service named by `BACKEND_SERVICE_NAME`.
- Nginx is already configured to serve HTTPS and the built frontend assets.
- The database env file already exists on the server at `/opt/financial-dashboard/.db.env` or `/opt/financial-dashboard/backend/.db.env`.
- The SSH user has sudo permission for:
  - `systemctl restart <BACKEND_SERVICE_NAME>`
  - `nginx -t`
  - `systemctl reload nginx`

## Database Env File

Do not commit `.db.env` to the repository and do not print its contents in GitHub Actions logs.

Create it directly on the server:

```bash
sudo install -d -o "$USER" -g "$USER" /opt/financial-dashboard
install -m 600 /dev/null /opt/financial-dashboard/.db.env
nano /opt/financial-dashboard/.db.env
```

Supported variable names:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=financial_dashboard
DB_PASSWORD=replace-with-real-password
DB_NAME=financial_dashboard
```

The backend also accepts the `FD_MARIADB_*` equivalents:

```dotenv
FD_MARIADB_HOST=127.0.0.1
FD_MARIADB_PORT=3306
FD_MARIADB_USER=financial_dashboard
FD_MARIADB_PASSWORD=replace-with-real-password
FD_MARIADB_DATABASE=financial_dashboard
```

The deploy workflow checks that one of these files exists before restarting the backend:

- `/opt/financial-dashboard/.db.env`
- `/opt/financial-dashboard/backend/.db.env`
