import pyodbc

# กำหนดค่าการเชื่อมต่อ
server = 'Servername'       # เช่น 'localhost' หรือ '192.168.1.10'
database = 'login'   # ชื่อฐานข้อมูล
username = 'sa'        # ชื่อผู้ใช้
password = 'Thanadol02'        # รหัสผ่าน

# สร้าง connection string
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

try:
    # เชื่อมต่อกับ SQL Server
    conn = pyodbc.connect(conn_str)
    print("✅ เชื่อมต่อสำเร็จ!")

    # สร้าง cursor เพื่อทำงานกับ database
    cursor = conn.cursor()

    # ตัวอย่างการ query
    cursor.execute("SELECT TOP 10 * FROM YourTableName")

    for row in cursor.fetchall():
        print(row)

except Exception as e:
    print("❌ เกิดข้อผิดพลาด:", e)