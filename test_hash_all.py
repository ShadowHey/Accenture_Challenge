import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table('hospitals').select('*').execute()
for row in res.data:
    print(row['hospital_code'], row['password_hash'])
