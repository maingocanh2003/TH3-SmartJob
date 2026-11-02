-- SmartJob Sample Data for Development
-- Run: psql -U smartjob_user -d smartjob_db -h localhost -f docs/seed_data.sql

-- Users
INSERT INTO Users (email, password_hash, user_type) VALUES
('candidate1@smartjob.vn', 'pbkdf2_sha256$720000$salt1$hashhash1', 'candidate'),
('candidate2@smartjob.vn', 'pbkdf2_sha256$720000$salt2$hashhash2', 'candidate'),
('candidate3@smartjob.vn', 'pbkdf2_sha256$720000$salt3$hashhash3', 'candidate'),
('hr@techvn.com', 'pbkdf2_sha256$720000$salt4$hashhash4', 'company'),
('hr@fpt.vn', 'pbkdf2_sha256$720000$salt5$hashhash5', 'company'),
('hr@vng.vn', 'pbkdf2_sha256$720000$salt6$hashhash6', 'company'),
('hr@vingroup.vn', 'pbkdf2_sha256$720000$salt7$hashhash7', 'company'),
('hr@momo.vn', 'pbkdf2_sha256$720000$salt8$hashhash8', 'company')
ON CONFLICT (email) DO NOTHING;

-- Candidates
INSERT INTO Candidates (user_id, full_name, phone, desired_position, years_of_experience, summary, desired_salary)
SELECT u.user_id, 'Nguyen Van An', '0901234567', 'Backend Developer', 3,
  'Lap trinh vien Backend voi 3 nam kinh nghiem Python, Django, PostgreSQL. Dam me xay dung he thong scalable.',
  20000000
FROM Users u WHERE u.email = 'candidate1@smartjob.vn'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Candidates (user_id, full_name, phone, desired_position, years_of_experience, summary, desired_salary)
SELECT u.user_id, 'Tran Thi Binh', '0912345678', 'Frontend Developer', 2,
  'Frontend Developer voi 2 nam kinh nghiem React, TypeScript. Chu trong UX/UI va performance.',
  15000000
FROM Users u WHERE u.email = 'candidate2@smartjob.vn'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Candidates (user_id, full_name, phone, desired_position, years_of_experience, summary, desired_salary)
SELECT u.user_id, 'Le Van Cuong', '0923456789', 'Data Scientist', 4,
  'Data Scientist voi 4 nam kinh nghiem Machine Learning, Python, TensorFlow. Chuyen phan tich du lieu lon.',
  25000000
FROM Users u WHERE u.email = 'candidate3@smartjob.vn'
ON CONFLICT (user_id) DO NOTHING;

-- Companies
INSERT INTO Companies (user_id, company_name, industry, company_size, address, description, website)
SELECT u.user_id, 'TechVN Solutions', 'IT', '100-500', 'Ha Noi',
  'Cong ty cong nghe hang dau Viet Nam, chuyen phat trien phan mem va giai phap AI.',
  'https://techvn.com'
FROM Users u WHERE u.email = 'hr@techvn.com'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Companies (user_id, company_name, industry, company_size, address, description, website)
SELECT u.user_id, 'FPT Software', 'IT', '10000+', 'Ha Noi',
  'Tap doan FPT - Doanh nghiep cong nghe lon nhat Viet Nam voi hon 10,000 nhan vien toan cau.',
  'https://fpt-software.com'
FROM Users u WHERE u.email = 'hr@fpt.vn'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Companies (user_id, company_name, industry, company_size, address, description, website)
SELECT u.user_id, 'VNG Corporation', 'IT', '5000+', 'Ho Chi Minh',
  'VNG la tap doan cong nghe hang dau voi cac san pham nhu Zalo, ZaloPay.',
  'https://vng.com.vn'
FROM Users u WHERE u.email = 'hr@vng.vn'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Companies (user_id, company_name, industry, company_size, address, description, website)
SELECT u.user_id, 'Vingroup Technology', 'IT', '1000-5000', 'Ha Noi',
  'Vingroup Technology - Don vi cong nghe cua Tap doan Vingroup.',
  'https://vingroup.net'
FROM Users u WHERE u.email = 'hr@vingroup.vn'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO Companies (user_id, company_name, industry, company_size, address, description, website)
SELECT u.user_id, 'MoMo Payment', 'Fintech', '500-1000', 'Ho Chi Minh',
  'MoMo - Vi dien tu so 1 Viet Nam voi hon 30 trieu nguoi dung.',
  'https://momo.vn'
FROM Users u WHERE u.email = 'hr@momo.vn'
ON CONFLICT (user_id) DO NOTHING;

-- Jobs
INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Senior Backend Developer (Python/Django)',
  'Chung toi dang tim kiem mot Senior Backend Developer co kinh nghiem va dam me xay dung cac he thong backend scalable. Ban se lam viec voi doi ngu ky su tai nang de xay dung cac API va microservices phuc vu hang trieu nguoi dung.',
  'Co kinh nghiem 3+ nam voi Python va Django. Hieu biet ve PostgreSQL, Redis. Kinh nghiem voi Docker, CI/CD. Ky nang giao tiep tot.',
  'Luong canh tranh, bao hiem suc khoe, bonus theo hieu suat, moi truong lam viec than thien.',
  'Senior', 'full-time', 3, 20000000, 35000000, 'Ha Noi', 3,
  CURRENT_DATE + INTERVAL '30 days', 'active'
FROM Companies c WHERE c.company_name = 'TechVN Solutions';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Frontend Developer (React/TypeScript)',
  'TechVN Solutions tuyen dung Frontend Developer co kinh nghiem voi React va TypeScript de xay dung giao dien nguoi dung cho cac san pham SaaS.',
  'Thao thao React, TypeScript, HTML/CSS. Biet Redux hoac Zustand. Hieu biet co ban ve REST API va GraphQL.',
  'Luong 15-25 trieu, lam viec flexible, team building hang quy.',
  'Mid', 'full-time', 2, 15000000, 25000000, 'Ha Noi', 2,
  CURRENT_DATE + INTERVAL '25 days', 'active'
FROM Companies c WHERE c.company_name = 'TechVN Solutions';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Java Backend Developer',
  'FPT Software tuyen dung Java Backend Developer lam viec voi cac du an lon cho khach hang nuoc ngoai. Co hoi lam viec voi cac cong nghe hien dai va doi ngu chuyen nghiep.',
  'Kinh nghiem 2+ nam Java va Spring Boot. Hieu biet microservices. Anh van tao tu cho du an nuoc ngoai.',
  'Luong canh tranh, co hoi di nuoc ngoai, dao tao chuyen sau.',
  'Mid', 'full-time', 5, 18000000, 30000000, 'Ha Noi', 2,
  CURRENT_DATE + INTERVAL '45 days', 'active'
FROM Companies c WHERE c.company_name = 'FPT Software';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Data Scientist / Machine Learning Engineer',
  'VNG tim kiem Data Scientist tai nang de phan tich du lieu nguoi dung va xay dung cac mo hinh ML cho Zalo va cac san pham cua VNG.',
  'Kinh nghiem Machine Learning, Deep Learning. Thanh thao Python, TensorFlow/PyTorch. Hieu biet Big Data (Spark).',
  'Luong toi 50 trieu, co phieu chung khoan, moi truong startup.',
  'Senior', 'full-time', 2, 30000000, 50000000, 'Ho Chi Minh', 3,
  CURRENT_DATE + INTERVAL '20 days', 'active'
FROM Companies c WHERE c.company_name = 'VNG Corporation';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'DevOps Engineer',
  'VNG tuyen DevOps Engineer de quan ly ha tang cloud quy mo lon phuc vu hang trieu nguoi dung Zalo.',
  'Kinh nghiem Docker, Kubernetes, AWS hoac GCP. Hieu biet CI/CD, Infrastructure as Code. Linux proficient.',
  'Luong 25-40 trieu, bonus, team outing.',
  'Mid', 'full-time', 2, 25000000, 40000000, 'Ho Chi Minh', 3,
  CURRENT_DATE + INTERVAL '30 days', 'active'
FROM Companies c WHERE c.company_name = 'VNG Corporation';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Fullstack Developer (Node.js + React)',
  'MoMo tuyen Fullstack Developer de xay dung tinh nang moi cho ung dung thanh toan di dong so 1 Viet Nam.',
  'Kinh nghiem Node.js, Express, React. Hieu biet bao mat payment. Kinh nghiem MongoDB.',
  'Luong 20-35 trieu, co phieu, moi truong fintech thu vi.',
  'Mid', 'full-time', 3, 20000000, 35000000, 'Ho Chi Minh', 2,
  CURRENT_DATE + INTERVAL '30 days', 'active'
FROM Companies c WHERE c.company_name = 'MoMo Payment';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'AI/ML Engineer - Computer Vision',
  'Vingroup Technology tuyen AI Engineer chuyen ve Computer Vision de xay dung cac giai phap nhan dang hinh anh cho VinSmart va VinFast.',
  'Kinh nghiem Computer Vision, OpenCV, YOLO. Thanh thao Python, PyTorch. Biet C++ la loi the.',
  'Luong hap dan, co hoi lam viec voi du an quoc gia lon.',
  'Senior', 'full-time', 2, 35000000, 60000000, 'Ha Noi', 4,
  CURRENT_DATE + INTERVAL '40 days', 'active'
FROM Companies c WHERE c.company_name = 'Vingroup Technology';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'React Native Mobile Developer',
  'TechVN tuyen React Native Developer xay dung ung dung mobile cross-platform cho khach hang trong nuoc va quoc te.',
  'Kinh nghiem React Native 1+ nam. Hieu biet iOS va Android. Redux, API integration.',
  'Luong 12-20 trieu, remote friendly, MacBook.',
  'Junior', 'full-time', 2, 12000000, 20000000, 'Ha Noi', 1,
  CURRENT_DATE + INTERVAL '20 days', 'active'
FROM Companies c WHERE c.company_name = 'TechVN Solutions';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Intern Backend Developer (Python)',
  'FPT Software tuyen intern Backend Developer Python cho sinh vien IT co am hieu co ban ve lap trinh web.',
  'Sinh vien nam 3-4 nganh CNTT. Biet Python co ban. Ham hoc hoi, chu dong.',
  'Allowance 3-5 trieu/thang, mentoring boi senior dev, co hoi full-time sau thuc tap.',
  'Intern', 'internship', 5, 3000000, 5000000, 'Ha Noi', 0,
  CURRENT_DATE + INTERVAL '15 days', 'active'
FROM Companies c WHERE c.company_name = 'FPT Software';

INSERT INTO Jobs (company_id, job_title, job_description, requirements, benefits, position_level, employment_type, num_of_positions, salary_min, salary_max, location, years_of_experience_required, application_deadline, status)
SELECT c.company_id,
  'Backend Developer (Go/Golang)',
  'VNG tuyen Backend Developer chuyen Go de xay dung cac microservices high-performance cho Zalo.',
  'Kinh nghiem Go 2+ nam. Hieu biet gRPC, Protocol Buffers. Kinh nghiem Redis, Kafka.',
  'Luong canh tranh, co phieu VNG, moi truong cong nghe cao.',
  'Mid', 'full-time', 3, 22000000, 38000000, 'Ho Chi Minh', 2,
  CURRENT_DATE + INTERVAL '35 days', 'active'
FROM Companies c WHERE c.company_name = 'VNG Corporation';

-- Candidate Skills
INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'advanced', 3
FROM Candidates can, Skills s
WHERE can.full_name = 'Nguyen Van An'
AND s.skill_name IN ('Python', 'Django', 'PostgreSQL', 'REST API', 'Git', 'Docker')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'intermediate', 3
FROM Candidates can, Skills s
WHERE can.full_name = 'Nguyen Van An'
AND s.skill_name IN ('Redis', 'AWS', 'Microservices')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'advanced', 2
FROM Candidates can, Skills s
WHERE can.full_name = 'Tran Thi Binh'
AND s.skill_name IN ('React', 'JavaScript', 'TypeScript', 'HTML/CSS')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'intermediate', 2
FROM Candidates can, Skills s
WHERE can.full_name = 'Tran Thi Binh'
AND s.skill_name IN ('Vue.js', 'Node.js', 'Git', 'Figma', 'REST API')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'advanced', 4
FROM Candidates can, Skills s
WHERE can.full_name = 'Le Van Cuong'
AND s.skill_name IN ('Python', 'Machine Learning', 'Deep Learning', 'Data Analysis', 'Statistics')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT can.candidate_id, s.skill_id, 'intermediate', 4
FROM Candidates can, Skills s
WHERE can.full_name = 'Le Van Cuong'
AND s.skill_name IN ('Natural Language Processing', 'Data Visualization', 'Big Data', 'AWS')
ON CONFLICT (candidate_id, skill_id) DO NOTHING;

-- Job Skills
INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'Senior Backend Developer (Python/Django)'
AND s.skill_name IN ('Python', 'Django', 'PostgreSQL', 'REST API')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'intermediate', false, 0.5
FROM Jobs j, Skills s
WHERE j.job_title = 'Senior Backend Developer (Python/Django)'
AND s.skill_name IN ('Docker', 'Redis', 'AWS', 'Microservices')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'Frontend Developer (React/TypeScript)'
AND s.skill_name IN ('React', 'TypeScript', 'JavaScript', 'HTML/CSS')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'intermediate', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'Java Backend Developer'
AND s.skill_name IN ('Java', 'Spring Boot', 'PostgreSQL', 'REST API', 'Microservices')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'Data Scientist / Machine Learning Engineer'
AND s.skill_name IN ('Python', 'Machine Learning', 'Deep Learning', 'Data Analysis', 'Statistics')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'DevOps Engineer'
AND s.skill_name IN ('Docker', 'Kubernetes', 'AWS', 'CI/CD')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'Fullstack Developer (Node.js + React)'
AND s.skill_name IN ('Node.js', 'React', 'JavaScript', 'MongoDB', 'REST API')
ON CONFLICT (job_id, skill_id) DO NOTHING;

INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required, weight)
SELECT j.job_id, s.skill_id, 'advanced', true, 1.0
FROM Jobs j, Skills s
WHERE j.job_title = 'AI/ML Engineer - Computer Vision'
AND s.skill_name IN ('Python', 'Deep Learning', 'Computer Vision', 'Machine Learning')
ON CONFLICT (job_id, skill_id) DO NOTHING;

-- Applications
INSERT INTO Applications (job_id, candidate_id, cover_letter, status)
SELECT j.job_id, c.candidate_id,
  'Toi rat quan tam den vi tri nay va tin rang ky nang cua minh phu hop voi yeu cau cua cong ty.',
  'pending'
FROM Jobs j, Candidates c
WHERE j.job_title = 'Senior Backend Developer (Python/Django)'
AND c.full_name = 'Nguyen Van An'
ON CONFLICT (job_id, candidate_id) DO NOTHING;

INSERT INTO Applications (job_id, candidate_id, cover_letter, status)
SELECT j.job_id, c.candidate_id,
  'Voi 2 nam kinh nghiem React, toi tu tin co the dong gop tich cuc cho team cua quy cong ty.',
  'reviewing'
FROM Jobs j, Candidates c
WHERE j.job_title = 'Frontend Developer (React/TypeScript)'
AND c.full_name = 'Tran Thi Binh'
ON CONFLICT (job_id, candidate_id) DO NOTHING;

INSERT INTO Applications (job_id, candidate_id, cover_letter, status)
SELECT j.job_id, c.candidate_id,
  'Voi 4 nam kinh nghiem Data Science va Machine Learning, toi mong muon duoc gop phan vao du an tai VNG.',
  'shortlisted'
FROM Jobs j, Candidates c
WHERE j.job_title = 'Data Scientist / Machine Learning Engineer'
AND c.full_name = 'Le Van Cuong'
ON CONFLICT (job_id, candidate_id) DO NOTHING;

-- Job Views for BI
INSERT INTO Job_Views (job_id, ip_address)
SELECT j.job_id, '192.168.1.' || generate_series(1, 10)
FROM Jobs j WHERE j.status = 'active';
