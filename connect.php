<?php
$serverName = "localhost";  // หรือชื่อเครื่อง/ชื่อ instance เช่น "TONNAM\SQLEXPRESS"
$connectionOptions = array(
    "Database" => "seminar",  // ชื่อฐานข้อมูล
    "Uid" => "sa",               // ชื่อผู้ใช้
    "PWD" => "123456",    // รหัสผ่าน
    "CharacterSet" => "UTF-8"    // ป้องกันภาษาเพี้ยน
);

// เชื่อมต่อ
$conn = sqlsrv_connect($serverName, $connectionOptions);

if ($conn === false) {
    die(print_r(sqlsrv_errors(), true));
} else {
    echo "เชื่อมต่อ SQL Server สำเร็จ!";
}
?>
