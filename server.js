const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const bcrypt = require("bcryptjs");
const sql = require("mssql");

// สร้าง express app
const app = express();

// ใช้งาน middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// SQL Server config
// หมายเหตุทั่วไป:
// - ข้อผิดพลาดที่คุณเจอเกิดจากการ lookup Named Instance (SQLEXPRESS) ไม่ได้
// - วิธีแก้เร็ว: ใช้พอร์ตคงที่ (เช่น 1433) และไม่ใช้ instanceName
// - ถ้าต้องใช้ named instance จริง ๆ ให้เปิด "SQL Server Browser" service หรือกำหนด Static TCP Port แล้วใส่ port ใน config
const DB_SERVER = process.env.DB_SERVER || 'localhost';
const DB_NAME = process.env.DB_NAME || 'seminar';
const DB_USER = process.env.DB_USER || 'sa';
const DB_PASS = process.env.DB_PASS || '123456';
const DB_INSTANCE = process.env.DB_INSTANCE || '';
const DB_PORT = Number(process.env.DB_PORT || 1433);

const dbConfig = {
    user: DB_USER,
    password: DB_PASS,
    server: DB_SERVER,
    database: DB_NAME,
    options: {
        trustServerCertificate: true,
        encrypt: true
    }
};
// ถ้ามีการระบุ INSTANCE ผ่าน env ให้ใช้ instanceName; ไม่งั้นใช้พอร์ตคงที่
if (DB_INSTANCE) {
    dbConfig.options.instanceName = DB_INSTANCE;
} else {
    dbConfig.port = DB_PORT;
}

// ใช้ Connection Pool เชื่อมครั้งเดียว
const poolPromise = new sql.ConnectionPool(dbConfig)
    .connect()
    .then(pool => {
        const mode = DB_INSTANCE ? `instance ${DB_INSTANCE}` : `port ${dbConfig.port}`;
        console.log(`✅ MSSQL connected (${DB_SERVER} → ${mode})`);
        return pool;
    })
    .catch(err => {
        console.error('❌ MSSQL connection failed:', err);
        // อย่า throw เพื่อไม่ให้โปรเซสล้ม — ให้ routes จัดการ error ต่อไป
        return null;
    });

// Health check
app.get('/health', async (_req, res) => {
    try {
        const pool = await poolPromise;
        await pool.request().query('SELECT 1 as ok');
        res.json({ ok: true });
    } catch (err) {
        res.status(500).json({ ok: false, error: String(err) });
    }
});

// Signup route
app.post("/signup", async (req, res) => {
    const { name, email, password } = req.body;
    if (!name || !email || !password) return res.status(400).json({ message: 'ข้อมูลไม่ครบ' });

    try {
        const pool = await poolPromise;

        // ตรวจอีเมลซ้ำ
        const check = await pool.request()
            .input('email', sql.NVarChar(255), email)
            .query('SELECT 1 FROM users WHERE email = @email');
        if (check.recordset.length > 0) {
            return res.status(400).json({ message: "อีเมลนี้ถูกใช้ไปแล้ว" });
        }

        // hash password
        const hashed = await bcrypt.hash(password, 10);

        // insert user
        await pool.request()
            .input('name', sql.NVarChar(100), name)
            .input('email', sql.NVarChar(255), email)
            .input('password', sql.NVarChar(255), hashed)
            .query('INSERT INTO users (username, email, password_hash) VALUES (@name, @email, @password)');

        res.json({ message: "สมัครสมาชิกสำเร็จ" });
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: "เกิดข้อผิดพลาด" });
    }
});

// Login route
app.post('/login', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) return res.status(400).json({ message: 'ข้อมูลไม่ครบ' });

    try {
        const pool = await poolPromise;
        const result = await pool.request()
            .input('email', sql.NVarChar(255), email)
            .query('SELECT TOP 1 id, username, email, password_hash FROM users WHERE email = @email');

        if (result.recordset.length === 0) {
            return res.status(401).json({ message: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' });
        }

        const user = result.recordset[0];
        const ok = await bcrypt.compare(password, user.password_hash);
        if (!ok) return res.status(401).json({ message: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' });

        // ส่งข้อมูลผู้ใช้บางส่วนกลับ (อย่าส่ง password_hash)
        res.json({
            message: 'เข้าสู่ระบบสำเร็จ',
            user: { id: user.id, name: user.username, email: user.email }
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'เกิดข้อผิดพลาด' });
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
