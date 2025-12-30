-- Adds model_answer and rubric fields for essay grading configuration.
ALTER TABLE question_templates
    ADD COLUMN IF NOT EXISTS model_answer text,
    ADD COLUMN IF NOT EXISTS rubric jsonb;

ALTER TABLE assessment_question_snapshots
    ADD COLUMN IF NOT EXISTS model_answer text,
    ADD COLUMN IF NOT EXISTS rubric jsonb;
