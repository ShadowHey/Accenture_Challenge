import bcrypt

hash_str = "$2b$12$Z050a4.3yvI5q/x7M1f5.udX2g78/69wL3Z3zHk/3990N.z99uX0O"
words = ["A001", "password", "password123", "admin", "admin123", "H001", "1234", "test"]

for w in words:
    if bcrypt.checkpw(w.encode('utf-8'), hash_str.encode('utf-8')):
        print(f"Match found: {w}")
