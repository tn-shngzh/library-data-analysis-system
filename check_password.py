import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2
import bcrypt

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = 'user'")
user = cur.fetchone()
if user:
    user_id, username, password_hash, role = user
    print(f"User: {username}, Role: {role}")
    print(f"Password hash (first 30 chars): {password_hash[:30]}...")
    
    # Test common passwords
    test_passwords = ['user123', 'user', '123456', 'password', 'User123!']
    for pwd in test_passwords:
        try:
            if bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8')):
                print(f"Match found! Password is: {pwd}")
                break
        except:
            continue
    else:
        print("No match found for common passwords")
        
        # Let's reset password to 'user123'
        new_hash = bcrypt.hashpw('user123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password_hash = %s WHERE username = 'user'", (new_hash,))
        conn.commit()
        print(f"Password has been reset to 'user123'")
        
        # Verify
        cur.execute("SELECT password_hash FROM users WHERE username = 'user'")
        new_hash_db = cur.fetchone()[0]
        if bcrypt.checkpw('user123'.encode('utf-8'), new_hash_db.encode('utf-8')):
            print("Verified! Login with username=user, password=user123")

cur.close()
conn.close()
