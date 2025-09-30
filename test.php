<?php
// ตั้งค่าการเชื่อมต่อ SQL Server
$serverName = "localhost,1433";   // หรือ IP + port
$connectionOptions = array(
    "Database" => "seminar",
    "Uid" => "sa",               
    "PWD" => "123456",
    "CharacterSet" => "UTF-8"
);

// เชื่อมต่อ
$conn = sqlsrv_connect($serverName, $connectionOptions);

if ($conn === false) {
    die(print_r(sqlsrv_errors(), true));
}

// รับค่าจากฟอร์ม (POST)
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST["username"] ?? "";
    $email = $_POST["email"] ?? "";
    $password = $_POST["password"] ?? "";

    // เข้ารหัส password
    $passwordHash = password_hash($password, PASSWORD_DEFAULT);

    // SQL Insert
    $sql = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)";
    $params = array($username, $email, $passwordHash);

    $stmt = sqlsrv_query($conn, $sql, $params);

    if ($stmt === false) {
        die(print_r(sqlsrv_errors(), true));
    } else {
        echo "สมัครสมาชิกสำเร็จ!";
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
</form>

      
    </section>
  </main>
</body>
</html>
