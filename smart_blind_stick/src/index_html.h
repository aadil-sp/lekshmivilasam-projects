#pragma once

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Smart Blind Stick Dashboard</title>
  <style>
    :root {
      --bg-dark: #0a0f1d;
      --card-bg: rgba(20, 27, 45, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #00f2ff;
      --accent-blue: #0072ff;
      --color-safe: #00e676;
      --color-warn: #ffab00;
      --color-danger: #ff1744;
      --text-main: #f0f4f8;
      --text-muted: #8a99ad;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    body {
      background: radial-gradient(circle at top center, #141f36 0%, var(--bg-dark) 100%);
      color: var(--text-main);
      min-height: 100vh;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .container {
      width: 100%;
      max-width: 520px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    header {
      text-align: center;
      padding: 10px 0 6px;
    }

    .header-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(0, 242, 255, 0.12);
      border: 1px solid rgba(0, 242, 255, 0.3);
      color: var(--accent-cyan);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 4px 12px;
      border-radius: 20px;
      margin-bottom: 8px;
    }

    .header-badge .pulse-dot {
      width: 7px;
      height: 7px;
      background: var(--accent-cyan);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-cyan);
      animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.9); opacity: 0.7; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.7; }
    }

    h1 {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 0%, var(--accent-cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .subtitle {
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
      transition: all 0.3s ease;
    }

    .emergency-banner {
      display: none;
      background: linear-gradient(135deg, rgba(255, 23, 68, 0.95), rgba(183, 0, 32, 0.95));
      border: 2px solid #ff5252;
      border-radius: 18px;
      padding: 20px;
      text-align: center;
      box-shadow: 0 0 35px rgba(255, 23, 68, 0.75);
      animation: emergencyPulse 0.8s infinite alternate;
    }

    @keyframes emergencyPulse {
      from { transform: scale(1); box-shadow: 0 0 20px rgba(255, 23, 68, 0.6); }
      to { transform: scale(1.02); box-shadow: 0 0 45px rgba(255, 23, 68, 1); }
    }

    .emergency-banner.active {
      display: block;
    }

    .emergency-title {
      font-size: 22px;
      font-weight: 900;
      color: #ffffff;
      text-transform: uppercase;
      letter-spacing: 1px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .emergency-desc {
      font-size: 14px;
      color: #ffebee;
      margin-top: 8px;
      font-weight: 500;
      line-height: 1.4;
    }

    .btn-silence {
      margin-top: 14px;
      background: #ffffff;
      color: #b70020;
      border: none;
      padding: 10px 24px;
      border-radius: 12px;
      font-size: 15px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0,0,0,0.25);
      transition: transform 0.15s;
    }

    .btn-silence:active {
      transform: scale(0.95);
    }

    .gauge-card {
      text-align: center;
      position: relative;
      overflow: hidden;
    }

    .distance-display {
      margin: 10px 0;
      display: flex;
      justify-content: center;
      align-items: baseline;
      gap: 6px;
    }

    .distance-value {
      font-size: 64px;
      font-weight: 900;
      font-feature-settings: "tnum";
      letter-spacing: -2px;
      transition: color 0.3s;
    }

    .distance-unit {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-muted);
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 18px;
      border-radius: 30px;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
      transition: all 0.3s ease;
    }

    .status-safe {
      background: rgba(0, 230, 118, 0.15);
      color: var(--color-safe);
      border: 1px solid rgba(0, 230, 118, 0.4);
    }

    .status-warn {
      background: rgba(255, 171, 0, 0.15);
      color: var(--color-warn);
      border: 1px solid rgba(255, 171, 0, 0.4);
    }

    .status-danger {
      background: rgba(255, 23, 68, 0.18);
      color: var(--color-danger);
      border: 1px solid rgba(255, 23, 68, 0.5);
      animation: dangerFlash 1s infinite alternate;
    }

    .bar-container {
      background: rgba(255, 255, 255, 0.06);
      height: 12px;
      border-radius: 6px;
      overflow: hidden;
      margin: 10px 0;
      position: relative;
    }

    .distance-bar {
      height: 100%;
      width: 0%;
      border-radius: 6px;
      background: linear-gradient(90deg, var(--color-danger) 0%, var(--color-warn) 30%, var(--color-safe) 70%);
      transition: width 0.25s ease-out;
    }

    .fall-timer-card {
      border-left: 4px solid var(--accent-cyan);
    }

    .timer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .timer-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .timer-val {
      font-size: 15px;
      font-weight: 800;
      font-feature-settings: "tnum";
    }

    .fall-progress-bar {
      height: 100%;
      width: 0%;
      border-radius: 6px;
      background: linear-gradient(90deg, #ffab00, #ff1744);
      transition: width 0.2s linear;
    }

    .timer-helper {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 6px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .stat-box {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 14px;
      padding: 14px;
    }

    .stat-label {
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 16px;
      font-weight: 800;
      margin-top: 4px;
      color: #ffffff;
    }

    .audio-card {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .audio-status-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .btn-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: var(--text-main);
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .btn:hover {
      background: rgba(255, 255, 255, 0.14);
    }

    .btn:active {
      transform: scale(0.97);
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-cyan) 100%);
      border: none;
      color: #051329;
      font-weight: 800;
      box-shadow: 0 4px 15px rgba(0, 242, 255, 0.3);
    }

    .btn-danger {
      background: linear-gradient(135deg, #d50000 0%, #ff1744 100%);
      border: none;
      color: #fff;
    }

    footer {
      text-align: center;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 10px;
      padding-bottom: 16px;
    }
  </style>
</head>
<body>

  <div class="container">

    <header>
      <div class="header-badge">
        <div class="pulse-dot"></div>
        <span>ESP8266 Live Hotspot (192.168.4.1)</span>
      </div>
      <h1>Smart Blind Stick</h1>
      <p class="subtitle">Arduino Nano & Ultrasonic Fall Detection Telemetry</p>
    </header>

    <!-- EMERGENCY ALERT BANNER -->
    <div id="emergencyBanner" class="emergency-banner">
      <div class="emergency-title">
        <span>🚨</span> EMERGENCY: MAN FELL DOWN! <span>🚨</span>
      </div>
      <p class="emergency-desc" id="emergencyBannerDesc">
        <strong>CRITICAL ALERT!</strong><br>
        Obstacle/Ground detected within 20 cm for over 10 seconds.<br>
        Audible siren and spoken voice alarm are active!
      </p>
      <button class="btn-silence" onclick="resetAlarm()">SILENCE & RESET ALARM</button>
    </div>

    <!-- MAIN DISTANCE GAUGE -->
    <div class="card gauge-card">
      <div id="statusPill" class="status-pill status-safe">
        <span>●</span> <span id="statusText">Scanning Path: Safe</span>
      </div>

      <div class="distance-display">
        <span id="distVal" class="distance-value">--</span>
        <span class="distance-unit">cm</span>
      </div>

      <div class="bar-container">
        <div id="distBar" class="distance-bar" style="width: 50%;"></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted);">
        <span>0 cm (Fall Zone)</span>
        <span>20 cm</span>
        <span>50 cm (Caution)</span>
        <span>200+ cm</span>
      </div>
    </div>

    <!-- 10-SECOND FALL DETECTION TIMER -->
    <div class="card fall-timer-card">
      <div class="timer-header">
        <span class="timer-title">⏱️ Fall Detection Timer (&le; 20 cm)</span>
        <span id="timerVal" class="timer-val">0.0s / 10.0s</span>
      </div>
      <div class="bar-container" style="height: 14px;">
        <div id="fallBar" class="fall-progress-bar"></div>
      </div>
      <div class="timer-helper" id="timerHelper">
        Hold stick horizontally or near ground &lt; 20 cm to test 10s automatic trigger.
      </div>
    </div>

    <!-- AUDIO CONTROLS CARD -->
    <div class="card audio-card">
      <div class="audio-status-row">
        <div>
          <strong style="font-size: 14px;">🔊 Browser Alarm & Voice</strong>
          <div style="font-size: 12px; color: var(--text-muted);" id="audioStatusText">Tap to Enable Sound</div>
        </div>
        <button id="btnEnableAudio" class="btn btn-primary" onclick="initAndTestAudio()" style="padding: 8px 14px;">
          Enable Sound
        </button>
      </div>

      <div class="btn-group">
        <button class="btn" onclick="testSiren()">🔔 Test Siren Sound</button>
        <button class="btn btn-danger" onclick="triggerManualTest()">🚨 Test Fall Alarm</button>
      </div>
    </div>

    <!-- STATS GRID -->
    <div class="stats-grid">
      <div class="stat-box">
        <div class="stat-label">Arduino Nano (D5)</div>
        <div class="stat-value" id="nanoStat" style="font-size: 15px; color: var(--color-safe);">Connected 🟢</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Switch State (D6)</div>
        <div class="stat-value" id="switchStat" style="font-size: 15px; color: #ffffff;">Normal</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Fall Threshold</div>
        <div class="stat-value">&le; 20 cm (10s)</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Telemetry Latency</div>
        <div class="stat-value" id="pingRate">~250 ms</div>
      </div>
    </div>

    <footer>
      Smart Blind Stick &copy; 2026 Lekshmivilasam. Ultrasonic & Switch Telemetry on ESP8266.
    </footer>

  </div>

  <script>
    let audioCtx = null;
    let sirenInterval = null;
    let isSirenPlaying = false;
    let audioUnlocked = false;
    let lastAlarmState = false;
    let speechTimer = null;

    function initAudio() {
      if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      audioUnlocked = true;
      document.getElementById('audioStatusText').innerText = 'Audio Ready & Armed 🟢';
      document.getElementById('btnEnableAudio').innerText = 'Audio Armed ✓';
      document.getElementById('btnEnableAudio').classList.remove('btn-primary');
    }

    function initAndTestAudio() {
      initAudio();
      beep(880, 0.15, 'sine');
      speak("Browser alarm armed.");
    }

    function beep(freq = 880, duration = 0.2, type = 'sawtooth') {
      try {
        if (!audioCtx) initAudio();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
      } catch (e) {}
    }

    function startEmergencySiren(customText = null) {
      if (isSirenPlaying) return;
      initAudio();
      isSirenPlaying = true;

      let high = false;
      sirenInterval = setInterval(() => {
        if (!isSirenPlaying) return;
        beep(high ? 1760 : 980, 0.25, 'sawtooth');
        high = !high;
      }, 260);

      const msg = customText || "Warning! Emergency! The user has fallen down! Please assist immediately!";
      speak(msg);
      if (speechTimer) clearInterval(speechTimer);
      speechTimer = setInterval(() => {
        if (isSirenPlaying) {
          speak(msg);
        }
      }, 7000);
    }

    function stopEmergencySiren() {
      isSirenPlaying = false;
      if (sirenInterval) {
        clearInterval(sirenInterval);
        sirenInterval = null;
      }
      if (speechTimer) {
        clearInterval(speechTimer);
        speechTimer = null;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    }

    function speak(text) {
      try {
        if ('speechSynthesis' in window) {
          const utter = new SpeechSynthesisUtterance(text);
          utter.rate = 1.1;
          utter.pitch = 1.2;
          utter.volume = 1.0;
          window.speechSynthesis.speak(utter);
        }
      } catch (e) {}
    }

    function testSiren() {
      initAudio();
      startEmergencySiren();
      setTimeout(() => {
        stopEmergencySiren();
      }, 3500);
    }

    function triggerManualTest() {
      fetch('/test_alarm', { method: 'POST' }).catch(() => {});
      startEmergencySiren();
      document.getElementById('emergencyBanner').classList.add('active');
    }

    function resetAlarm() {
      stopEmergencySiren();
      fetch('/reset_alarm', { method: 'POST' }).catch(() => {});
      document.getElementById('emergencyBanner').classList.remove('active');
    }

    async function updateTelemetry() {
      const startTime = performance.now();
      try {
        const response = await fetch('/data');
        if (!response.ok) throw new Error("HTTP error " + response.status);
        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        document.getElementById('pingRate').innerText = `${latency} ms`;

        const distValEl = document.getElementById('distVal');
        const statusPill = document.getElementById('statusPill');
        const statusText = document.getElementById('statusText');
        const distBar = document.getElementById('distBar');
        const nanoStat = document.getElementById('nanoStat');
        const switchStat = document.getElementById('switchStat');
        const banner = document.getElementById('emergencyBanner');

        // Nano Connection
        if (data.nanoConnected) {
          nanoStat.innerText = 'Connected 🟢';
          nanoStat.style.color = 'var(--color-safe)';
        } else {
          nanoStat.innerText = 'Offline 🔴';
          nanoStat.style.color = 'var(--color-danger)';
        }

        // Switch State
        if (data.switchPressed) {
          switchStat.innerText = '🚨 SOS PRESSED!';
          switchStat.style.color = 'var(--color-danger)';
        } else {
          switchStat.innerText = 'Normal (Released)';
          switchStat.style.color = '#ffffff';
        }

        // Distance Value
        const dist = Math.round(data.distance * 10) / 10;
        distValEl.innerText = dist > 400 || dist <= 0 ? "--" : dist.toFixed(1);

        const barPct = Math.min(100, Math.max(5, (dist / 150) * 100));
        distBar.style.width = `${barPct}%`;

        // 10s Fall Timer
        const fallTimerSec = (data.fallTimer || 0).toFixed(1);
        const maxSec = data.alarmSeconds || 10.0;
        document.getElementById('timerVal').innerText = `${fallTimerSec}s / ${maxSec}.0s`;
        const fallPct = Math.min(100, ((data.fallTimer || 0) / maxSec) * 100);
        document.getElementById('fallBar').style.width = `${fallPct}%`;

        if (data.isAlarm) {
          statusPill.className = 'status-pill status-danger';
          statusText.innerText = '🚨 CRITICAL: MAN FELL DOWN!';
          distValEl.style.color = 'var(--color-danger)';
          banner.classList.add('active');

          if (!isSirenPlaying) {
            startEmergencySiren(data.switchPressed ? "Emergency SOS button pressed! Assist user now!" : "Warning! Emergency! The user has fallen down!");
          }
        } else {
          banner.classList.remove('active');
          if (isSirenPlaying && lastAlarmState) {
            stopEmergencySiren();
          }

          if (dist <= 20 && dist > 0) {
            statusPill.className = 'status-pill status-danger';
            statusText.innerText = '⚠️ CRITICAL PROXIMITY (< 20cm)';
            distValEl.style.color = 'var(--color-danger)';
            document.getElementById('timerHelper').innerText = `Fall countdown active! Alarm triggers in ${(maxSec - data.fallTimer).toFixed(1)}s!`;
          } else if (dist <= 50 && dist > 20) {
            statusPill.className = 'status-pill status-warn';
            statusText.innerText = '⚠️ OBSTACLE NEARBY (< 50cm)';
            distValEl.style.color = 'var(--color-warn)';
            document.getElementById('timerHelper').innerText = 'Obstacle in path. Slow down / navigate around.';
          } else {
            statusPill.className = 'status-pill status-safe';
            statusText.innerText = '✓ SCANNING PATH: CLEAR';
            distValEl.style.color = 'var(--color-safe)';
            document.getElementById('timerHelper').innerText = 'Normal walking. Fall timer resets automatically.';
          }
        }

        lastAlarmState = data.isAlarm;

      } catch (err) {
        document.getElementById('pingRate').innerText = 'Offline';
      }
    }

    document.addEventListener('click', () => {
      if (!audioUnlocked) initAudio();
    }, { once: true });

    setInterval(updateTelemetry, 250);
    updateTelemetry();
  </script>
</body>
</html>
)rawliteral";
