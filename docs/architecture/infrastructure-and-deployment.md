# Infrastructure and Deployment
- **Infrastructure as Code:**  
  - Tool: Terraform 1.7.3 for AWS (future), plus Railway/Render configuration files.  
  - Location: `infra/railway`, `infra/render`, `infra/aws/terraform`.  
  - Approach: Keep Railway/Render configs under version control; Terraform modules dormant until budget allows AWS migration.

- **Deployment Strategy:**  
  - Local development uses Docker Compose with Postgres and Redis containers.  
  - Staging & production run on Railway (or Render) free tiers; document resource limits and autosleep.  
  - CI/CD via GitHub Actions (`.github/workflows/deploy.yml`) running lint → tests → OpenAPI export → deploy via platform CLI.  
  - AWS ECS Fargate reference pipeline commented out for future scale-up.

- **Environments:**  
  - Local dev – developer workstations.  
  - Staging – Railway/Render service mirroring production settings.  
  - Production – Railway/Render primary runtime with monitoring of quota usage.  
  - Future migration – AWS ECS Fargate and RDS modules ready when funding allows.

- **Promotion Flow:** `local-dev → staging (Railway/Render) → production (Railway/Render) → [later] AWS`.

- **Rollback Strategy:**  
  - Primary: Revert Railway/Render deployment to prior image/commit.  
  - Triggers: 5xx spike, async queue backlog >100 for 5 minutes, latency >10s, recommendation generation failures.  
  - Recovery Time Objective: ~5 minutes (platform rollback); database restore via platform snapshots if needed.
