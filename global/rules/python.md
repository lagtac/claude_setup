---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

# Python (uv) Commands

- **Run script:** `uv run <script.py>`
- **Install deps:** `uv sync`
- **Add dep:** `uv add <package>` (requires approval)
- **Test:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Format:** `uv run ruff format .`
