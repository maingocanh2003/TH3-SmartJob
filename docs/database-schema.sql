-- =====================================================
-- SMARTJOB DATABASE SCHEMA
-- PostgreSQL Database Creation Script
-- =====================================================

-- =====================================================
-- 1. CREATE TABLES
-- =====================================================

-- Table: Users
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('candidate', 'company', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Candidates
CREATE TABLE Candidates (
    candidate_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    gender VARCHAR(10),
    avatar_url TEXT,
    summary TEXT,
    desired_position VARCHAR(255),
    desired_salary DECIMAL(10,2),
    years_of_experience INTEGER,
    cv_file_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Companies
CREATE TABLE Companies (
    company_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    tax_code VARCHAR(50) UNIQUE,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    address TEXT,
    phone VARCHAR(20),
    website VARCHAR(255),
    logo_url TEXT,
    description TEXT,
    contact_person VARCHAR(255),
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Skills
CREATE TABLE Skills (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Candidate_Skills
CREATE TABLE Candidate_Skills (
    candidate_skill_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES Skills(skill_id) ON DELETE CASCADE,
    proficiency_level VARCHAR(50) CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_of_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_id, skill_id)
);

-- Table: Education
CREATE TABLE Education (
    education_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    institution_name VARCHAR(255) NOT NULL,
    degree VARCHAR(100),
    major VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Experience
CREATE TABLE Experience (
    experience_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    responsibilities TEXT,
    achievements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Jobs
CREATE TABLE Jobs (
    job_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES Companies(company_id) ON DELETE CASCADE,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    requirements TEXT,
    benefits TEXT,
    position_level VARCHAR(50),
    employment_type VARCHAR(50) CHECK (employment_type IN ('full-time', 'part-time', 'contract', 'internship')),
    num_of_positions INTEGER DEFAULT 1,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(10) DEFAULT 'VND',
    location VARCHAR(255),
    years_of_experience_required INTEGER,
    application_deadline DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'draft')),
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Job_Skills
CREATE TABLE Job_Skills (
    job_skill_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES Jobs(job_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES Skills(skill_id) ON DELETE CASCADE,
    required_level VARCHAR(50) CHECK (required_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    is_required BOOLEAN DEFAULT TRUE,
    weight DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, skill_id)
);

-- Table: Applications
CREATE TABLE Applications (
    application_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES Jobs(job_id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    cover_letter TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected', 'withdrawn')),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, candidate_id)
);

-- Table: AI_Match_Results
CREATE TABLE AI_Match_Results (
    match_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES Jobs(job_id) ON DELETE CASCADE,
    matching_score DECIMAL(5,2) NOT NULL CHECK (matching_score >= 0 AND matching_score <= 100),
    matched_skills JSONB,
    missing_skills JSONB,
    skill_match_details JSONB,
    experience_match DECIMAL(5,2),
    education_match DECIMAL(5,2),
    salary_match DECIMAL(5,2),
    overall_recommendation VARCHAR(50) CHECK (overall_recommendation IN ('highly_recommended', 'recommended', 'potential', 'not_recommended')),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Job_Views
CREATE TABLE Job_Views (
    view_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES Jobs(job_id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES Candidates(candidate_id) ON DELETE SET NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Saved_Jobs
CREATE TABLE Saved_Jobs (
    saved_job_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES Candidates(candidate_id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES Jobs(job_id) ON DELETE CASCADE,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(candidate_id, job_id)
);

-- =====================================================
-- 2. CREATE INDEXES
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_users_type ON Users(user_type);

-- Candidates indexes
CREATE INDEX idx_candidates_user_id ON Candidates(user_id);
CREATE INDEX idx_candidates_desired_position ON Candidates(desired_position);

-- Companies indexes
CREATE INDEX idx_companies_user_id ON Companies(user_id);
CREATE INDEX idx_companies_industry ON Companies(industry);

-- Jobs indexes
CREATE INDEX idx_jobs_company_id ON Jobs(company_id);
CREATE INDEX idx_jobs_status ON Jobs(status);
CREATE INDEX idx_jobs_location ON Jobs(location);
CREATE INDEX idx_jobs_deadline ON Jobs(application_deadline);
CREATE INDEX idx_jobs_created_at ON Jobs(created_at DESC);

-- Applications indexes
CREATE INDEX idx_applications_job_id ON Applications(job_id);
CREATE INDEX idx_applications_candidate_id ON Applications(candidate_id);
CREATE INDEX idx_applications_status ON Applications(status);
CREATE INDEX idx_applications_applied_at ON Applications(applied_at DESC);

-- Skills indexes
CREATE INDEX idx_skills_name ON Skills(skill_name);
CREATE INDEX idx_skills_category ON Skills(category);

-- AI Match Results indexes
CREATE INDEX idx_match_candidate_id ON AI_Match_Results(candidate_id);
CREATE INDEX idx_match_job_id ON AI_Match_Results(job_id);
CREATE INDEX idx_match_score ON AI_Match_Results(matching_score DESC);
CREATE INDEX idx_match_calculated_at ON AI_Match_Results(calculated_at DESC);

-- Job Views indexes (for BI)
CREATE INDEX idx_job_views_job_id ON Job_Views(job_id);
CREATE INDEX idx_job_views_date ON Job_Views(viewed_at);

-- =====================================================
-- 3. CREATE TRIGGERS
-- =====================================================

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON Users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidates_updated_at 
    BEFORE UPDATE ON Candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON Companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON Jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at 
    BEFORE UPDATE ON Applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function: Auto-increment job view count
CREATE OR REPLACE FUNCTION increment_job_view_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Jobs SET view_count = view_count + 1 WHERE job_id = NEW.job_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_view_count 
    AFTER INSERT ON Job_Views
    FOR EACH ROW EXECUTE FUNCTION increment_job_view_count();

-- =====================================================
-- 4. INSERT SAMPLE DATA
-- =====================================================

-- Insert sample skills
INSERT INTO Skills (skill_name, category) VALUES
('Python', 'Programming Language'),
('Java', 'Programming Language'),
('JavaScript', 'Programming Language'),
('TypeScript', 'Programming Language'),
('C++', 'Programming Language'),
('C#', 'Programming Language'),
('PHP', 'Programming Language'),
('Ruby', 'Programming Language'),
('Go', 'Programming Language'),
('Rust', 'Programming Language'),
('React', 'Frontend Framework'),
('Angular', 'Frontend Framework'),
('Vue.js', 'Frontend Framework'),
('Django', 'Backend Framework'),
('Flask', 'Backend Framework'),
('Spring Boot', 'Backend Framework'),
('Node.js', 'Backend Framework'),
('Express.js', 'Backend Framework'),
('Laravel', 'Backend Framework'),
('Ruby on Rails', 'Backend Framework'),
('PostgreSQL', 'Database'),
('MySQL', 'Database'),
('MongoDB', 'Database'),
('Redis', 'Database'),
('Oracle', 'Database'),
('Microsoft SQL Server', 'Database'),
('Machine Learning', 'AI/ML'),
('Deep Learning', 'AI/ML'),
('Natural Language Processing', 'AI/ML'),
('Computer Vision', 'AI/ML'),
('Data Analysis', 'Data Science'),
('Data Visualization', 'Data Science'),
('Statistics', 'Data Science'),
('Big Data', 'Data Science'),
('AWS', 'Cloud Platform'),
('Azure', 'Cloud Platform'),
('Google Cloud Platform', 'Cloud Platform'),
('Docker', 'DevOps'),
('Kubernetes', 'DevOps'),
('CI/CD', 'DevOps'),
('Git', 'Version Control'),
('HTML/CSS', 'Web Development'),
('REST API', 'API Development'),
('GraphQL', 'API Development'),
('Microservices', 'Architecture'),
('System Design', 'Architecture'),
('Communication', 'Soft Skills'),
('Teamwork', 'Soft Skills'),
('Problem Solving', 'Soft Skills'),
('Leadership', 'Soft Skills'),
('Time Management', 'Soft Skills'),
('Critical Thinking', 'Soft Skills'),
('Project Management', 'Management'),
('Agile/Scrum', 'Methodology'),
('Waterfall', 'Methodology'),
('Testing/QA', 'Quality Assurance'),
('Unit Testing', 'Quality Assurance'),
('Integration Testing', 'Quality Assurance'),
('Security', 'Cybersecurity'),
('Network Security', 'Cybersecurity'),
('Mobile Development', 'Mobile'),
('iOS Development', 'Mobile'),
('Android Development', 'Mobile'),
('React Native', 'Mobile'),
('Flutter', 'Mobile'),
('UI/UX Design', 'Design'),
('Figma', 'Design'),
('Adobe XD', 'Design'),
('Photoshop', 'Design'),
('Business Analysis', 'Business'),
('Sales', 'Business'),
('Marketing', 'Business'),
('SEO', 'Marketing'),
('Content Marketing', 'Marketing');

-- =====================================================
-- END OF SCRIPT
-- =====================================================
