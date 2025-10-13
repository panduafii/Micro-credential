# Security (Simplified Standards)
- Validate inputs with FastAPI/Pydantic at every boundary; prefer allow-lists for enums.  
- Authenticate with JWT bearer tokens (PyJWT) and bcrypt password hashing (cost 12); enforce role checks via dependencies.  
- Manage secrets through `.env` locally and Railway/Render environment variables in production; never commit secrets.  
- Enable slowapi rate limiting (60 req/min default), restrict CORS to trusted origins, and enforce HTTPS via platform settings.  
- Rely on managed Postgres/Redis encryption at rest; use TLS for outbound calls; never log assessment answers or tokens.  
- Run Dependabot and `pip-audit` monthly; remediate critical CVEs immediately.  
- Include Semgrep OSS scan in CI and run OWASP ZAP baseline against staging before releases.
