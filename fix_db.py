import os
import bcrypt
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

hashed = bcrypt.hashpw(b"A001", bcrypt.gensalt()).decode('utf-8')
supabase.table('hospitals').update({'password_hash': hashed}).eq('hospital_code', 'H001').execute()
print("Updated H001 password to A001")
