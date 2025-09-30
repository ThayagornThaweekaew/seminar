// --- Focus Timer System ---
let timer = null;
let timeLeft = 0;
let isRunning = false;

let subjects = JSON.parse(localStorage.getItem("subjects")) || ["คณิต", "อังกฤษ", "ฟิสิกส์"];
let subjectTimes = JSON.parse(localStorage.getItem("subjectTimes")) || {};
let totalFocus = JSON.parse(localStorage.getItem("totalFocus")) || 0;
let todayDate = new Date().toDateString();
let todayFocus = JSON.parse(localStorage.getItem("todayFocus")) || { date: todayDate, minutes: 0 };

function renderSubjects() {
  const sel = document.getElementById("subjectSelect");
  sel.innerHTML = "";
  subjects.forEach(sub => {
    let opt = document.createElement("option");
    opt.value = sub;
    opt.textContent = sub;
    sel.appendChild(opt);
  });
  document.getElementById("subjectsCount").textContent = subjects.length;
}

function addSubject() {
  const newSub = document.getElementById("newSubject").value.trim();
  if (newSub && !subjects.includes(newSub)) {
    subjects.push(newSub);
    localStorage.setItem("subjects", JSON.stringify(subjects));
    renderSubjects();
  }
  document.getElementById("newSubject").value = "";
}

function startTimer() {
  if (isRunning) return;
  const minutes = parseInt(document.getElementById("timeSelect").value);
  timeLeft = minutes * 60;
  isRunning = true;
  updateDisplay();

  timer = setInterval(() => {
    timeLeft--;
    updateDisplay();
    if (timeLeft <= 0) {
      clearInterval(timer);
      isRunning = false;
      saveTime(minutes);
      alert("หมดเวลา!");
    }
  }, 1000);
}

function pauseTimer() {
  clearInterval(timer);
  isRunning = false;
}

function stopTimer() {
  clearInterval(timer);
  isRunning = false;
  timeLeft = 0;
  updateDisplay();
}

function updateDisplay() {
  const min = String(Math.floor(timeLeft / 60)).padStart(2, "0");
  const sec = String(timeLeft % 60).padStart(2, "0");
  document.getElementById("display").textContent = `${min}:${sec}`;
}

function saveTime(minutes) {
  const sub = document.getElementById("subjectSelect").value;
  subjectTimes[sub] = (subjectTimes[sub] || 0) + minutes;
  localStorage.setItem("subjectTimes", JSON.stringify(subjectTimes));

  totalFocus += minutes;
  localStorage.setItem("totalFocus", JSON.stringify(totalFocus));

  if (todayFocus.date !== todayDate) {
    todayFocus = { date: todayDate, minutes: 0 };
  }
  todayFocus.minutes += minutes;
  localStorage.setItem("todayFocus", JSON.stringify(todayFocus));

  document.getElementById("totalTime").textContent = Math.floor(totalFocus / 60) + "h";
  document.getElementById("todayTime").textContent = todayFocus.minutes + "m";
  document.getElementById("sessions").textContent =
    parseInt(document.getElementById("sessions").textContent) + 1;

  renderLog();
}

function renderLog() {
  const ul = document.getElementById("subjectLog");
  ul.innerHTML = "";
  for (let sub in subjectTimes) {
    let li = document.createElement("li");
    li.textContent = `${sub}: ${subjectTimes[sub]} นาที`;
    ul.appendChild(li);
  }
}

// --- Digital Clock ---
function updateDigitalClock() {
  const now = new Date();
  document.getElementById("digitalClock").textContent =
    now.toLocaleTimeString("th-TH", { hour12: false });
}
setInterval(updateDigitalClock, 1000);
updateDigitalClock();

// --- Analog Clock ---
function updateAnalogClock(){
  const now = new Date();
  const s = now.getSeconds(), m = now.getMinutes(), h = now.getHours();
  document.querySelector('.hand.second').style.transform=`translate(-50%,-100%) rotate(${s*6}deg)`;
  document.querySelector('.hand.minute').style.transform=`translate(-50%,-100%) rotate(${m*6+s*0.1}deg)`;
  document.querySelector('.hand.hour').style.transform=`translate(-50%,-100%) rotate(${(h%12)*30+m*0.5}deg)`;
}
setInterval(updateAnalogClock,1000); updateAnalogClock();

// --- Calendar ---
function renderCalendar(){
  const today = new Date(),
        y = today.getFullYear(),
        m = today.getMonth();
  const firstDay = new Date(y, m, 1);
  const lastDate = new Date(y, m+1, 0).getDate();
  const startDay = firstDay.getDay();

  const head = document.getElementById('calHead'),
        grid = document.getElementById('calGrid');
  
  const monthNames = ["January","February","March","April","May","June","July",
                      "August","September","October","November","December"];
  
  head.textContent = `${monthNames[m]} ${y}`;
  grid.innerHTML = "";

  const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  for(const dn of dayNames){
    let d=document.createElement("div");
    d.className="cell muted";
    d.textContent=dn;
    grid.appendChild(d);
  }

  for(let i=0;i<startDay;i++){
    let empty=document.createElement("div");
    empty.className="cell muted";
    grid.appendChild(empty);
  }

  for(let d=1;d<=lastDate;d++){
    let c=document.createElement("div");
    c.className="cell";
    c.textContent=d;
    if(d===today.getDate()) c.classList.add("today");
    grid.appendChild(c);
  }
}

renderCalendar();

// Init
renderSubjects();
renderLog();
document.getElementById("totalTime").textContent = Math.floor(totalFocus / 60) + "h";
document.getElementById("todayTime").textContent = todayFocus.minutes + "m";
renderCalendar();
