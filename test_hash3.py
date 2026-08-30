from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_str = "$2b$12$Z050a4.3yvI5q/x7M1f5.udX2g78/69wL3Z3zHk/3990N.z99uX0O"
words = ["A001", "password", "password123", "admin", "admin123", "H001", "1234", "test", "0000"]
for w in words:
    if pwd_context.verify(w, hash_str):
        print(f"Match: {w}")
