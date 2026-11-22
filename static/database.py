import sqlite3

def get_connection():
    conn = sqlite3.connect("locations.db")

    return conn

def create_table():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS locations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL
        )
    """)

    conn.commit
    conn.close()

def add_location(room_code,category):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO LOCATIONS (room_code, category)
            VALUES(?,?)
        """,(room_code,category))
        
    except sqlite3.IntegrityError:
        print("Classroom already exists")   

    finally:
        conn.close()   
