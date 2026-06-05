-- Schema setup for opencourseware (run against the opencourseware database)

-- Enums
DO $$ BEGIN
  CREATE TYPE jobstatus AS ENUM ('pending', 'running', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE courselevel AS ENUM ('undergraduate', 'graduate', 'professional', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Tables
CREATE TABLE IF NOT EXISTS scraper_jobs (
  source VARCHAR(50) NOT NULL,
  status jobstatus NOT NULL,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  courses_scraped INTEGER NOT NULL DEFAULT 0,
  videos_scraped INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  config_json TEXT,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_scraper_jobs_source ON scraper_jobs (source);
CREATE INDEX IF NOT EXISTS ix_scraper_jobs_status ON scraper_jobs (status);

CREATE TABLE IF NOT EXISTS subjects (
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  description TEXT,
  parent_id UUID,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  FOREIGN KEY (parent_id) REFERENCES subjects(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_subjects_name ON subjects (name);
CREATE INDEX IF NOT EXISTS ix_subjects_parent_id ON subjects (parent_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_subjects_slug ON subjects (slug);

CREATE TABLE IF NOT EXISTS universities (
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  description TEXT,
  website VARCHAR(500),
  logo_url VARCHAR(500),
  country VARCHAR(100),
  youtube_channel_id VARCHAR(100),
  source_key VARCHAR(50) NOT NULL,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_universities_name ON universities (name);
CREATE UNIQUE INDEX IF NOT EXISTS ix_universities_slug ON universities (slug);
CREATE INDEX IF NOT EXISTS ix_universities_source_key ON universities (source_key);

CREATE TABLE IF NOT EXISTS users (
  email VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS departments (
  university_id UUID NOT NULL,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  description TEXT,
  code VARCHAR(50),
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  FOREIGN KEY (university_id) REFERENCES universities(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_departments_name ON departments (name);
CREATE INDEX IF NOT EXISTS ix_departments_slug ON departments (slug);
CREATE INDEX IF NOT EXISTS ix_departments_university_id ON departments (university_id);

CREATE TABLE IF NOT EXISTS courses (
  university_id UUID NOT NULL,
  department_id UUID,
  course_number VARCHAR(50),
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(600) NOT NULL,
  description TEXT,
  level courselevel NOT NULL,
  source_url VARCHAR(1000),
  source_key VARCHAR(50) NOT NULL,
  thumbnail_url VARCHAR(500),
  instructor VARCHAR(255),
  year INTEGER,
  semester VARCHAR(30),
  has_video_lectures BOOLEAN NOT NULL DEFAULT FALSE,
  has_lecture_notes BOOLEAN NOT NULL DEFAULT FALSE,
  has_exams BOOLEAN NOT NULL DEFAULT FALSE,
  lecture_notes_url VARCHAR(1000),
  exams_url VARCHAR(1000),
  youtube_playlist_id VARCHAR(100),
  total_videos INTEGER NOT NULL DEFAULT 0,
  total_duration_seconds INTEGER NOT NULL DEFAULT 0,
  view_count INTEGER NOT NULL DEFAULT 0,
  is_published BOOLEAN NOT NULL DEFAULT FALSE,
  search_vector TEXT,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  FOREIGN KEY (university_id) REFERENCES universities(id) ON DELETE CASCADE,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_courses_course_number ON courses (course_number);
CREATE INDEX IF NOT EXISTS ix_courses_department_id ON courses (department_id);
CREATE INDEX IF NOT EXISTS ix_courses_level ON courses (level);
CREATE INDEX IF NOT EXISTS ix_courses_is_published ON courses (is_published);
CREATE UNIQUE INDEX IF NOT EXISTS ix_courses_slug ON courses (slug);
CREATE INDEX IF NOT EXISTS ix_courses_source_key ON courses (source_key);
CREATE INDEX IF NOT EXISTS ix_courses_source_key_number ON courses (source_key, course_number);
CREATE INDEX IF NOT EXISTS ix_courses_title ON courses (title);
CREATE INDEX IF NOT EXISTS ix_courses_university_id ON courses (university_id);
CREATE INDEX IF NOT EXISTS ix_courses_university_level ON courses (university_id, level);
CREATE INDEX IF NOT EXISTS ix_courses_youtube_playlist_id ON courses (youtube_playlist_id);

CREATE TABLE IF NOT EXISTS course_subjects (
  course_id UUID NOT NULL,
  subject_id UUID NOT NULL,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  UNIQUE (course_id, subject_id)
);

CREATE TABLE IF NOT EXISTS videos (
  course_id UUID NOT NULL,
  youtube_id VARCHAR(20) NOT NULL,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  thumbnail_url VARCHAR(500),
  duration_seconds INTEGER,
  "order" INTEGER NOT NULL DEFAULT 0,
  published_at TIMESTAMP WITH TIME ZONE,
  view_count BIGINT,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_videos_course_id ON videos (course_id);
CREATE INDEX IF NOT EXISTS ix_videos_youtube_id ON videos (youtube_id);

CREATE TABLE IF NOT EXISTS alembic_version (
  version_num VARCHAR(32) NOT NULL,
  PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('abb770ac77cb') ON CONFLICT DO NOTHING;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ocw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ocw;
GRANT USAGE ON TYPE courselevel TO ocw;
GRANT USAGE ON TYPE jobstatus TO ocw;

SELECT 'Schema setup complete!' AS result;
