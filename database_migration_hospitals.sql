-- Create Hospitals Table
CREATE TABLE IF NOT EXISTS hospitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    hospital_code TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Historical Records Table
CREATE TABLE IF NOT EXISTS historical_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID REFERENCES hospitals(id),
    patient_name TEXT,
    age INTEGER,
    gender TEXT,
    chief_complaint TEXT,
    vitals JSONB,
    medical_history JSONB,
    observed_signs JSONB,
    visit_date TEXT,
    discharge_status TEXT,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert Initial Hospitals
INSERT INTO hospitals (name, hospital_code, password_hash) 
VALUES ('A Hospital', 'H001', '$2b$12$udSp87HsycD4KSOw56S.K.DwQ5C1atLnoAJ53rEl0PIkOx/diVRCS')
ON CONFLICT (hospital_code) DO NOTHING;

INSERT INTO hospitals (name, hospital_code, password_hash) 
VALUES ('B Hospital', 'H002', '$2b$12$y8QljR057zPrpDLlMKb9fubdB7mxWXxXWUlrptJXRDTZv6tNugHdm')
ON CONFLICT (hospital_code) DO NOTHING;
