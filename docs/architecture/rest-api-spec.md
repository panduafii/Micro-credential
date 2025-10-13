# REST API Spec
```yaml
openapi: 3.0.0
info:
  title: AI Micro-Credential Assessment API
  version: 0.1.0
  description: >
    REST API powering asynchronous assessments, scoring, and recommendations.
servers:
  - url: https://api.microcred.local/v1
    description: Staging environment (Railway)
  - url: https://api.microcred.prod/v1
    description: Production environment
security:
  - bearerAuth: []
paths:
  /assessments/start:
    post:
      tags: [Assessments]
      summary: Start a new assessment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AssessmentStartRequest'
      responses:
        '201':
          description: Assessment created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssessmentStartResponse'
        '400':
          description: Invalid role or missing prerequisites
        '401':
          description: Unauthorized
  /assessments/{assessment_id}/responses:
    post:
      tags: [Assessments]
      summary: Submit responses batch
      parameters:
        - $ref: '#/components/parameters/AssessmentId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AssessmentResponseBatch'
      responses:
        '202':
          description: Accepted; async processing queued when complete
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssessmentSubmissionAck'
        '400':
          description: Invalid payload or assessment state
        '404':
          description: Assessment not found
  /assessments/{assessment_id}:
    get:
      tags: [Assessments]
      summary: Get assessment status
      parameters:
        - $ref: '#/components/parameters/AssessmentId'
      responses:
        '200':
          description: Status payload
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssessmentStatus'
        '404':
          description: Not found
  /assessments/{assessment_id}/result:
    get:
      tags: [Assessments, Recommendations]
      summary: Retrieve final recommendation result
      parameters:
        - $ref: '#/components/parameters/AssessmentId'
      responses:
        '200':
          description: Recommendation ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssessmentResult'
        '202':
          description: Still processing
        '404':
          description: Not found
  /recommendations/{recommendation_id}/feedback:
    post:
      tags: [Recommendations]
      summary: Submit feedback for a recommendation
      parameters:
        - $ref: '#/components/parameters/RecommendationId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RecommendationFeedbackRequest'
      responses:
        '201':
          description: Feedback recorded
        '400':
          description: Invalid payload
        '404':
          description: Recommendation not found
  /catalog/credentials:
    get:
      tags: [Catalog]
      summary: List credential catalog entries
      parameters:
        - in: query
          name: role_id
          schema:
            type: string
          description: Optional filter by role
        - in: query
          name: page
          schema:
            type: integer
            minimum: 1
            default: 1
        - in: query
          name: page_size
          schema:
            type: integer
            minimum: 10
            maximum: 100
            default: 25
      responses:
        '200':
          description: Paginated credential list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CredentialList'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  parameters:
    AssessmentId:
      name: assessment_id
      in: path
      required: true
      schema:
        type: string
    RecommendationId:
      name: recommendation_id
      in: path
      required: true
      schema:
        type: string
  schemas:
    AssessmentStartRequest:
      type: object
      required: [role_id]
      properties:
        role_id:
          type: string
        metadata:
          type: object
          additionalProperties: true
    AssessmentStartResponse:
      type: object
      required: [assessment_id, status, questions]
      properties:
        assessment_id:
          type: string
        status:
          type: string
          enum: [in_progress, completed, awaiting_async]
        expires_at:
          type: string
          format: date-time
        questions:
          type: array
          items:
            $ref: '#/components/schemas/QuestionSnapshot'
    QuestionSnapshot:
      type: object
      required: [question_id, type, prompt, rubric]
      properties:
        question_id:
          type: string
        type:
          type: string
          enum: [multiple_choice, essay, profile]
        prompt:
          type: string
        choices:
          type: array
          items:
            type: string
          nullable: true
        rubric:
          type: object
          additionalProperties: true
        version:
          type: string
    AssessmentResponseBatch:
      type: object
      required: [responses]
      properties:
        responses:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/AssessmentResponseItem'
        completed:
          type: boolean
    AssessmentResponseItem:
      type: object
      required: [question_id, answer]
      properties:
        question_id:
          type: string
        answer:
          oneOf:
            - type: string
            - type: number
            - type: object
              additionalProperties: true
        submitted_at:
          type: string
          format: date-time
    AssessmentSubmissionAck:
      type: object
      required: [assessment_id, status, async_job_enqueued]
      properties:
        assessment_id:
          type: string
        status:
          type: string
          enum: [in_progress, awaiting_async, completed]
        async_job_enqueued:
          type: boolean
        message:
          type: string
    AssessmentStatus:
      type: object
      required: [assessment_id, status, progress, degraded]
      properties:
        assessment_id:
          type: string
        status:
          type: string
          enum: [in_progress, awaiting_async, completed, failed]
        progress:
          type: object
          properties:
            answered:
              type: integer
            total:
              type: integer
        degraded:
          type: boolean
        last_updated_at:
          type: string
          format: date-time
    AssessmentResult:
      type: object
      required: [assessment_id, summary, recommendation_items, traces, metrics, degraded]
      properties:
        assessment_id:
          type: string
        summary:
          type: string
        recommendation_items:
          type: array
          items:
            $ref: '#/components/schemas/RecommendationItem'
        traces:
          type: array
          items:
            $ref: '#/components/schemas/RagTrace'
        metrics:
          $ref: '#/components/schemas/ProcessingMetrics'
        degraded:
          type: boolean
        completed_at:
          type: string
          format: date-time
    RecommendationItem:
      type: object
      required: [credential_id, title, confidence, rationale]
      properties:
        credential_id:
          type: string
        title:
          type: string
        confidence:
          type: number
        rationale:
          type: string
        source_trace_ids:
          type: array
          items:
            type: string
    RagTrace:
      type: object
      required: [trace_id, source_uri, snippet, similarity]
      properties:
        trace_id:
          type: string
        source_uri:
          type: string
          format: uri
        snippet:
          type: string
        similarity:
          type: number
        embedding_provider:
          type: string
          enum: [sentence-transformers, openai]
    ProcessingMetrics:
      type: object
      required: [total_latency_ms, token_cost_cents]
      properties:
        total_latency_ms:
          type: integer
        token_cost_cents:
          type: number
        gpt_latency_ms:
          type: integer
        rag_latency_ms:
          type: integer
    RecommendationFeedbackRequest:
      type: object
      required: [relevance_score]
      properties:
        relevance_score:
          type: integer
          minimum: 1
          maximum: 5
        acceptance_status:
          type: string
          enum: [accepted, rejected, pending]
        comments:
          type: string
        submitted_by_role:
          type: string
          enum: [student, advisor]
    CredentialList:
      type: object
      required: [items, page, page_size, total]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Credential'
        page:
          type: integer
        page_size:
          type: integer
        total:
          type: integer
    Credential:
      type: object
      required: [credential_id, title, description, skills]
      properties:
        credential_id:
          type: string
        title:
          type: string
        description:
          type: string
        skills:
          type: array
          items:
            type: string
        provider:
          type: string
        embedding_vector_ref:
          type: string
          description: Reference for embedding artifact
    ErrorResponse:
      type: object
      required: [error_code, message]
      properties:
        error_code:
          type: string
        message:
          type: string
```
