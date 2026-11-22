import sqlite3

def get_connection():
    conn = sqlite3.connect("locations.db")
    conn.row_factory = sqlite3.Row
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

    conn.commit()
    conn.close()

def add_location(room_code,category):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO LOCATIONS (room_code, category)
            VALUES(?,?)
        """,(room_code,category))

        conn.commit()
        return True   
    except sqlite3.IntegrityError:
        print("Classroom already exists")   

    finally:
        conn.close()   

def view_locations():
    conn = get_connection()

    locations = conn.execute("""
        SELECT * FROM locations
        ORDER BY room_code
    """).fetchall()

    conn.close()

    return locations

def delete_location(location_id):
    conn = get_connection()
    cursor = conn.execute("""
        DELETE FROM locations
        WHERE id = ?
    """,(location_id,))

    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def update_location(location_id,room_code,category):
    conn = get_connection()
    
    try:
        cursor = conn.execute("""
            UPDATE locations

            SET room_code = ?,
                category =?
            
            WHERE id = ?
        """,(room_code,category,location_id))

        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()