import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = supabase.table('hospitals').select('*').execute()
    print("Hospitals in DB:")
    for row in res.data:
        print(f" - {row['hospital_code']}: {row['name']}")
except Exception as e:
    print(f"Error: {e}")
