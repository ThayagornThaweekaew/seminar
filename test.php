<?php
// ===== ตั้งค่าเชื่อมต่อ SQL Server =====
$serverName = "localhost,1433";
$dbOptions  = [
  "Database" => "seminar",
  "Uid" => "sa",
  "PWD" => "123456",
  "CharacterSet" => "UTF-8"
];

// ถ้า sqlsrv ยังไม่ถูกโหลด ให้ฟ้องชัด ๆ
if (!function_exists('sqlsrv_connect')) {
  die("❌ ยังไม่ได้เปิด extension sqlsrv/pdo_sqlsrv ใน PHP. ทำตามขั้นตอน: โหลด DLL ที่ตรงเวอร์ชัน → ใส่ใน php.ini → รีสตาร์ท Apache");
}

$conn = sqlsrv_connect($serverName, $dbOptions);
if ($conn === false) {
  die(print_r(sqlsrv_errors(), true));
}

$msg = "";
if ($_SERVER["REQUEST_METHOD"] === "POST") {
  $username = trim($_POST["username"] ?? "");
  $email    = trim($_POST["email"] ?? "");
  $password = $_POST["password"] ?? "";

  if ($username === "" || $email === "" || $password === "") {
    $msg = "กรอกข้อมูลให้ครบถ้วน";
  } else {
    $passwordHash = password_hash($password, PASSWORD_DEFAULT);

    // ป้องกันซ้ำด้วย UNIQUE ในตารางอยู่แล้ว, ถ้าอยากเช็คเองก็ SELECT ก่อน
    $sql    = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)";
    $params = [$username, $email, $passwordHash];
    $stmt   = sqlsrv_query($conn, $sql, $params);

    if ($stmt === false) {
      $errors = sqlsrv_errors();
      $msg = "บันทึกไม่สำเร็จ: " . ($errors ? $errors[0]['message'] : "unknown error");
    } else {
      $msg = "✅ สมัครสมาชิกสำเร็จ";
    }
  }
}
?>
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signup</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <main class="wrap">
    <section class="panel">
      <h1 class="title">Create an account</h1>
      <p class="muted">Join us to get started</p>

      <?php if ($msg): ?>
        <p style="margin:.5rem 0; padding:.5rem 1rem; border-radius:.5rem; background:#f3f4f6;">
          <?= htmlspecialchars($msg) ?>
        </p>
      <?php endif; ?>

      <form id="signupForm" class="grid" method="POST" action="">
        <label class="field">
          <span class="label">Username</span>
          <input class="input" type="text" name="username" placeholder="Username" required />
        </label>

        <label class="field">
          <span class="label">Email</span>
          <input class="input" type="email" name="email" placeholder="you@example.com" required />
        </label>

        <label class="field">
          <span class="label">Password</span>
          <input class="input" type="password" name="password" placeholder="••••••••" minlength="8" required />
        </label>

        <label class="field">
          <span class="label">Confirm password</span>
          <input class="input" type="password" id="confirm" placeholder="••••••••" minlength="8" required />
          <small id="matchMsg" style="font-size:13px;color:#ef4444;display:none;">
            Passwords do not match
          </small>
        </label>

        <button class="btn primary" type="submit">Create account</button>

        <p class="new-here">
          Already have an account?
          <a href="index.php" class="btn-ghost">Sign in</a>
        </p>
      </form>
    </section>
  </main>

  <script>
    // กันพิมพ์รหัสผ่านไม่ตรง
    const pwd = document.querySelector('input[name="password"]');
    const cfm = document.getElementById('confirm');
    const msg = document.getElementById('matchMsg');
    function checkMatch(){
      if (!pwd.value || !cfm.value) { msg.style.display='none'; return; }
      msg.style.display = (pwd.value === cfm.value) ? 'none' : 'block';
    }
    pwd.addEventListener('input', checkMatch);
    cfm.addEventListener('input', checkMatch);
  </script>
</body>
</html>
