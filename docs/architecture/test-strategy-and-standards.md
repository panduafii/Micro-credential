# Test Strategy and Standards
- **Testing Philosophy:** Hybrid approach—unit tests alongside implementation, integration tests before enabling features, smoke tests prior to releases. Coverage targets: ≥85% overall, ≥90% for scoring/recommendation domains; CI blocks drops >2%. Test pyramid: 60% unit, 30% integration, 10% end-to-end.
- **Unit Tests:** pytest 8.2.1; files in `tests/unit/<module>/test_<subject>.py`; mock external dependencies with pytest-mock/respx; maintain ≥90% coverage on domain modules; AI agents must cover edge/error paths and follow Arrange-Act-Assert.  
- **Integration Tests:** Located in `tests/integration/`; exercise API flows, async jobs, and repositories using Dockerized Postgres/Redis; reuse recorded OpenAI responses via respx fixtures.  
- **End-to-End Tests:** pytest + httpx AsyncClient hitting staging Railway deployment; cover start→result→feedback path with seeded data.  
- **Test Data Management:** Fixtures under `tests/fixtures/` (questions, credentials, async payloads); dynamic objects via `factory_boy`; database rolled back per test and Redis flushed between modules.  
- **Continuous Testing:** GitHub Actions pipeline runs lint → unit → integration → OpenAPI diff → deploy. Nightly workflow replays integration suite. Optional locust/k6 scripts for load smoke; Semgrep OSS rules run weekly.
