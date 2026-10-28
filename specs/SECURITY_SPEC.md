# SECURITY_SPEC.md

**Status:** Approved
**Version:** 1.0
**Last updated:** 2026-10-28

---

## 1. Threat Model

Graphora is a locally-run developer tool. Its primary threat surface is:

1. Credentials leaking into version control or logs.
2. Malformed or malicious document uploads causing server-side issues.
3. Prompt injection attacks via document content influencing extraction or generation.
4. Dependency vulnerabilities.
5. Unauthorized access if the API is exposed beyond localhost.

---

## 2. Secret Management

| Rule | Detail |
|------|--------|
| S-1 | All secrets (database passwords, LM Studio API keys if any, Redis passwords) are read from environment variables only. |
| S-2 | A `.env.example` file is committed with placeholder values. The `.env` file is gitignored. |
| S-3 | Secrets are never logged. Structured log entries containing connection strings must redact credentials. |
| S-4 | CI workflows use GitHub Actions secrets; they are never echoed in workflow steps. |
| S-5 | Docker Compose reads secrets from the `.env` file at runtime; secrets are not hardcoded in `docker-compose.yml`. |

**CI secret scanning:** `gitleaks` runs on every pull request and every push to main. A detected credential fails the CI check.

---

## 3. API Security

| Rule | Detail |
|------|--------|
| A-1 | In v1.0, the FastAPI backend binds to `127.0.0.1` by default, not `0.0.0.0`. It is not exposed to the network without explicit configuration. |
| A-2 | CORS is configured to allow only the frontend origin. The default allowed origin is `http://localhost:3000`. |
| A-3 | Request body size is limited to 100MB for file uploads. Requests exceeding this limit are rejected with HTTP 413. |
| A-4 | All API endpoints validate input using Pydantic models. No raw dict access from request bodies. |
| A-5 | Database queries use parameterized statements (SQLAlchemy ORM). Raw string interpolation into SQL is forbidden. |
| A-6 | Cypher queries constructed from user input use parameterized Cypher syntax. String interpolation into Cypher is forbidden. |

---

## 4. File Upload Security

| Rule | Detail |
|------|--------|
| F-1 | Uploaded files are validated by MIME type and file extension. Only PDF, TXT, MD, DOCX, and recognized archive types are accepted. |
| F-2 | Uploaded files are stored in a configurable upload directory outside the web root. They are not directly served over HTTP. |
| F-3 | File names from uploads are sanitized (path traversal characters removed) before writing to disk. |
| F-4 | Maximum file size per upload is 50MB (configurable). |
| F-5 | Web URL scraping is restricted to HTTP and HTTPS schemes. File:// and other schemes are rejected. |

---

## 5. Prompt Injection Awareness

Entity and relationship extraction operates on user-supplied document content. Adversarial content in documents could attempt to hijack extraction prompts.

| Rule | Detail |
|------|--------|
| P-1 | Extraction prompts use a fixed system message. Document content is passed as a clearly delimited user message. |
| P-2 | Extraction responses are parsed as JSON. Any text outside the expected JSON schema is discarded; it does not influence application state. |
| P-3 | Generation prompts delimit retrieved context clearly from the user query. Context is labeled as retrieved information, not as instructions. |
| P-4 | The application does not act on any instructions found within retrieved document content or generated answers. |

---

## 6. Dependency Security

| Rule | Detail |
|------|--------|
| D-1 | Python dependencies are pinned in `requirements.txt` (or `pyproject.toml` with locked versions via `uv`). |
| D-2 | Node.js dependencies are pinned via `package-lock.json` or `pnpm-lock.yaml`. |
| D-3 | GitHub Actions: `pip-audit` (Python) and `npm audit` (Node.js) run on every pull request. |
| D-4 | Dependabot or Renovate is configured to open automated PRs for dependency updates. |
| D-5 | Docker base images pin to a specific digest, not `latest`. |

---

## 7. Data Privacy

| Rule | Detail |
|------|--------|
| PV-1 | Document content is processed locally. It is sent only to the local LM Studio endpoint. It is never sent to an external API unless the developer explicitly changes the LM Studio base URL to an external endpoint. |
| PV-2 | Evaluation datasets (which may contain sensitive question-answer pairs) are stored in the local PostgreSQL database only. |
| PV-3 | No telemetry, analytics, or usage reporting is sent anywhere. |

---

## 8. Third-Party License Obligations

- A `NOTICE` file in the repository root acknowledges Apache 2.0 requirements.
- A `THIRD_PARTY_LICENSES.md` file lists every runtime dependency, its version, its license, and a link to its license text.
- Neo4j Community Edition (GPL-3.0) is documented as a runtime dependency; its source is not incorporated into the application.
- This file must be updated whenever a new runtime dependency is added.
