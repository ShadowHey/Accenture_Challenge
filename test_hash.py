import os
from supabase import create_client
from dotenv import load_dotenv
import bcrypt

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = supabase.table('hospitals').select('*').eq('hospital_code', 'H001').execute()
    if res.data:
        hosp = res.data[0]
        hash_str = hosp['password_hash']
        print(f"Hash in DB: {hash_str}")
        print("Checking 'A001':", bcrypt.checkpw(b'A001', hash_str.encode('utf-8')))
    else:
        print("Not found")
except Exception as e:
    print(f"Error: {e}")
