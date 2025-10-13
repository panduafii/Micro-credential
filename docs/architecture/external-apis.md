# External APIs
- **OpenAI API**  
  - Purpose: GPT essay scoring and fallback embeddings.  
  - Docs: https://platform.openai.com/docs/api-reference/introduction  
  - Base URL: `https://api.openai.com/v1`  
  - Auth: Bearer token via `Authorization: Bearer <OPENAI_API_KEY>`  
  - Endpoints: `POST /chat/completions`, `POST /embeddings`  
  - Notes: Use exponential backoff retries, record token usage for cost tracking.

- **Webhook Subscribers (Partner Systems)**  
  - Purpose: Notify advisor platforms when recommendations complete.  
  - Auth: HMAC signature with shared secret stored in platform env vars.  
  - Endpoint: `POST /webhooks/assessment-complete` (partner-defined).  
  - Notes: Store delivery attempts and responses; enable retries with dead-letter queue.
