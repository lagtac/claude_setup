---
paths:
  - "**/Dockerfile*"
  - "**/{docker-compose,compose}*.{yml,yaml}"
---

# Docker Commands

- **Start services:** `docker compose up -d`
- **Stop services:** `docker compose down`
- **Rebuild:** `docker compose build --no-cache`
- **Logs:** `docker compose logs -f <service>`
- **Exec into container:** `docker compose exec <service> bash`
