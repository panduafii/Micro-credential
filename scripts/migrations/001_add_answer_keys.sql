-- Adds answer key and scoring metadata columns for templates and snapshots.
ALTER TABLE question_templates
    ADD COLUMN IF NOT EXISTS difficulty varchar(32) DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS weight double precision NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS correct_answer varchar(255),
    ADD COLUMN IF NOT EXISTS answer_key text,
    ADD COLUMN IF NOT EXISTS expected_values jsonb;

ALTER TABLE assessment_question_snapshots
    ADD COLUMN IF NOT EXISTS difficulty varchar(32) DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS weight double precision NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS correct_answer varchar(255),
    ADD COLUMN IF NOT EXISTS answer_key text,
    ADD COLUMN IF NOT EXISTS expected_values jsonb;
