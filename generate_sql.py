from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_A = pwd_context.hash("A001")
hash_B = pwd_context.hash("B002")

sql = f"""
-- Insert Initial Hospitals
INSERT INTO hospitals (name, hospital_code, password_hash) 
VALUES ('A Hospital', 'H001', '{hash_A}')
ON CONFLICT (hospital_code) DO NOTHING;

INSERT INTO hospitals (name, hospital_code, password_hash) 
VALUES ('B Hospital', 'H002', '{hash_B}')
ON CONFLICT (hospital_code) DO NOTHING;
"""
with open('database_migration_hospitals.sql', 'a') as f:
    f.write(sql)
print("Done")
