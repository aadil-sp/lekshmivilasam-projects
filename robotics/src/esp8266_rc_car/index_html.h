#pragma once

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>RoboCar Wi-Fi Controller</title>
  <style>
    :root {
      --bg-dark: #070b14;
      --card-bg: rgba(16, 24, 40, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #00f2ff;
      --accent-orange: #ff9100;
      --accent-red: #ff1744;
      --accent-green: #00e676;
      --text-main: #f0f4f8;
      --text-muted: #8292a6;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
      -webkit-user-select: none;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    body {
      background: radial-gradient(circle at top center, #111d33 0%, var(--bg-dark) 100%);
      color: var(--text-main);
      min-height: 100vh;
      padding: 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      touch-action: manipulation;
    }

    .container {
      width: 100%;
      max-width: 480px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* HEADER */
    header {
      text-align: center;
      padding: 6px 0;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(0, 242, 255, 0.12);
      border: 1px solid rgba(0, 242, 255, 0.3);
      color: var(--accent-cyan);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 4px 12px;
      border-radius: 20px;
      margin-bottom: 6px;
    }

    .badge .dot {
      width: 7px;
      height: 7px;
      background: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 1.2s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.9); opacity: 0.7; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.7; }
    }

    h1 {
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 0%, var(--accent-cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .subtitle {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* CARD CONTAINER */
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    /* STATUS HUD */
    .hud-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      text-align: center;
    }

    .hud-box {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 12px;
      padding: 10px 6px;
    }

    .hud-label {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.5px;
    }

    .hud-value {
      font-size: 16px;
      font-weight: 900;
      color: var(--accent-cyan);
      margin-top: 4px;
    }

    /* VIRTUAL D-PAD CONTROLLER */
    .dpad-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      margin: 10px 0;
    }

    .dpad-row {
      display: flex;
      justify-content: center;
      gap: 10px;
      width: 100%;
    }

    .btn-ctrl {
      background: rgba(255, 255, 255, 0.06);
      border: 2px solid rgba(255, 255, 255, 0.12);
      color: #ffffff;
      width: 82px;
      height: 82px;
      border-radius: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      font-size: 26px;
      font-weight: 900;
      cursor: pointer;
      touch-action: none;
      transition: all 0.12s ease;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
    }

    .btn-ctrl span.key-hint {
      font-size: 10px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
    }

    .btn-ctrl:active, .btn-ctrl.active {
      transform: scale(0.92);
      background: linear-gradient(135deg, rgba(0, 242, 255, 0.3) 0%, rgba(0, 114, 255, 0.4) 100%);
      border-color: var(--accent-cyan);
      box-shadow: 0 0 25px rgba(0, 242, 255, 0.6);
      color: #ffffff;
    }

    .btn-stop {
      background: rgba(255, 23, 68, 0.15);
      border-color: rgba(255, 23, 68, 0.4);
      color: var(--accent-red);
    }

    .btn-stop:active, .btn-stop.active {
      background: linear-gradient(135deg, rgba(255, 23, 68, 0.5), rgba(183, 0, 32, 0.8));
      border-color: #ff5252;
      box-shadow: 0 0 25px rgba(255, 23, 68, 0.7);
      color: #fff;
    }

    /* SPEED PWM SLIDER */
    .slider-section {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .slider-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      font-weight: 700;
    }

    .speed-val {
      font-size: 15px;
      font-weight: 900;
      color: var(--accent-orange);
    }

    input[type=range] {
      width: 100%;
      height: 10px;
      border-radius: 5px;
      background: rgba(255, 255, 255, 0.08);
      outline: none;
      accent-color: var(--accent-cyan);
      cursor: pointer;
    }

    .preset-group {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-top: 4px;
    }

    .btn-preset {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      padding: 8px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.15s;
    }

    .btn-preset:hover, .btn-preset.active {
      background: rgba(0, 242, 255, 0.18);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }

    /* KEYBOARD CHEATSHEET */
    .keyboard-guide {
      font-size: 12px;
      color: var(--text-muted);
      text-align: center;
      line-height: 1.6;
    }

    .kbd-badge {
      display: inline-block;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 6px;
      padding: 2px 7px;
      font-weight: 800;
      color: #fff;
      font-size: 11px;
    }

    footer {
      text-align: center;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
      padding-bottom: 12px;
    }
  </style>
</head>
<body>

  <div class="container">

    <!-- HEADER -->
    <header>
      <div class="badge">
        <div class="dot"></div>
        <span>Open Wi-Fi Hotspot (192.168.4.1)</span>
      </div>
      <h1>RoboCar Controller</h1>
      <p class="subtitle">ESP8266 NodeMCU & L298N Dual PWM RC Platform</p>
    </header>

    <!-- STATUS HUD -->
    <div class="card">
      <div class="hud-grid">
        <div class="hud-box">
          <div class="hud-label">Drive State</div>
          <div class="hud-value" id="hudState">STOPPED</div>
        </div>
        <div class="hud-box">
          <div class="hud-label">PWM Speed</div>
          <div class="hud-value" id="hudSpeed" style="color: var(--accent-orange);">80%</div>
        </div>
        <div class="hud-box">
          <div class="hud-label">Latency</div>
          <div class="hud-value" id="hudPing">0 ms</div>
        </div>
      </div>
    </div>

    <!-- D-PAD CONTROLLER -->
    <div class="card">
      <div class="dpad-container">
        <!-- FORWARD ROW -->
        <div class="dpad-row">
          <button id="btnFwd" class="btn-ctrl" onmousedown="sendDrive('F')" onmouseup="sendDrive('S')" ontouchstart="sendDrive('F')" ontouchend="sendDrive('S')">
            ▲
            <span class="key-hint">W / UP</span>
          </button>
        </div>

        <!-- LEFT / STOP / RIGHT ROW -->
        <div class="dpad-row">
          <button id="btnLeft" class="btn-ctrl" onmousedown="sendDrive('L')" onmouseup="sendDrive('S')" ontouchstart="sendDrive('L')" ontouchend="sendDrive('S')">
            ◀
            <span class="key-hint">A / LEFT</span>
          </button>

          <button id="btnStop" class="btn-ctrl btn-stop" onclick="sendDrive('S')">
            🛑
            <span class="key-hint" style="color: #ff8a80;">SPACE</span>
          </button>

          <button id="btnRight" class="btn-ctrl" onmousedown="sendDrive('R')" onmouseup="sendDrive('S')" ontouchstart="sendDrive('R')" ontouchend="sendDrive('S')">
            ▶
            <span class="key-hint">D / RIGHT</span>
          </button>
        </div>

        <!-- REVERSE ROW -->
        <div class="dpad-row">
          <button id="btnRev" class="btn-ctrl" onmousedown="sendDrive('B')" onmouseup="sendDrive('S')" ontouchstart="sendDrive('B')" ontouchend="sendDrive('S')">
            ▼
            <span class="key-hint">S / DOWN</span>
          </button>
        </div>
      </div>
    </div>

    <!-- PWM SPEED CONTROLS -->
    <div class="card slider-section">
      <div class="slider-header">
        <span>⚡ Motor PWM Speed</span>
        <span class="speed-val" id="speedLabel">800 / 1023 (78%)</span>
      </div>

      <input type="range" id="speedSlider" min="300" max="1023" value="800" oninput="updateSpeed(this.value)">

      <div class="preset-group">
        <button class="btn-preset" onclick="setPreset(550)">🌱 Eco (55%)</button>
        <button class="btn-preset active" onclick="setPreset(800)">🚀 Normal (78%)</button>
        <button class="btn-preset" onclick="setPreset(1023)">🔥 Turbo (100%)</button>
      </div>
    </div>

    <!-- KEYBOARD HELP GUIDE -->
    <div class="card keyboard-guide">
      💻 <strong>Keyboard Controls:</strong> Use <span class="kbd-badge">W</span> <span class="kbd-badge">A</span> <span class="kbd-badge">S</span> <span class="kbd-badge">D</span> or <span class="kbd-badge">↑</span> <span class="kbd-badge">←</span> <span class="kbd-badge">↓</span> <span class="kbd-badge">→</span> to drive. Release key or press <span class="kbd-badge">Space</span> to brake.
    </div>

    <footer>
      RoboCar L298N Wi-Fi Edition &copy; 2026 Lekshmivilasam Robotics.
    </footer>

  </div>

  <script>
    let currentSpeed = 800;
    let currentDirection = 'S';
    let activeKeys = new Set();
    let heartbeatInterval = null;

    function updateSpeed(val) {
      currentSpeed = parseInt(val);
      const pct = Math.round((currentSpeed / 1023) * 100);
      document.getElementById('speedLabel').innerText = `${currentSpeed} / 1023 (${pct}%)`;
      document.getElementById('hudSpeed').innerText = `${pct}%`;

      if (currentDirection !== 'S') {
        sendDrive(currentDirection);
      }
    }

    function setPreset(val) {
      document.getElementById('speedSlider').value = val;
      updateSpeed(val);

      document.querySelectorAll('.btn-preset').forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');
    }

    // Fast asynchronous drive dispatcher
    function sendDrive(dir) {
      currentDirection = dir;
      updateDpadUI(dir);

      const startTime = performance.now();
      fetch(`/drive?dir=${dir}&speed=${currentSpeed}`, { method: 'GET', cache: 'no-store' })
        .then(res => {
          const latency = Math.round(performance.now() - startTime);
          document.getElementById('hudPing').innerText = `${latency} ms`;
        })
        .catch(err => {
          document.getElementById('hudPing').innerText = 'Offline';
        });

      // Maintain heartbeat while holding
      if (dir !== 'S') {
        if (!heartbeatInterval) {
          heartbeatInterval = setInterval(() => {
            if (currentDirection !== 'S') {
              fetch(`/drive?dir=${currentDirection}&speed=${currentSpeed}`, { method: 'GET', cache: 'no-store' }).catch(()=>{});
            }
          }, 300);
        }
      } else {
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          heartbeatInterval = null;
        }
      }
    }

    function updateDpadUI(dir) {
      const stateMap = {
        'F': 'FORWARD 🚀',
        'B': 'REVERSE 🔻',
        'L': 'TURNING LEFT ◀',
        'R': 'TURNING RIGHT ▶',
        'S': 'STOPPED 🛑'
      };
      document.getElementById('hudState').innerText = stateMap[dir] || 'STOPPED';

      // Reset active classes
      document.querySelectorAll('.btn-ctrl').forEach(b => b.classList.remove('active'));
      if (dir === 'F') document.getElementById('btnFwd').classList.add('active');
      else if (dir === 'B') document.getElementById('btnRev').classList.add('active');
      else if (dir === 'L') document.getElementById('btnLeft').classList.add('active');
      else if (dir === 'R') document.getElementById('btnRight').classList.add('active');
      else if (dir === 'S') document.getElementById('btnStop').classList.add('active');
    }

    // Keyboard WASD & Arrow Key Listeners
    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      const key = e.key.toLowerCase();
      activeKeys.add(key);

      if (key === 'w' || key === 'arrowup') {
        sendDrive('F');
      } else if (key === 's' || key === 'arrowdown') {
        sendDrive('B');
      } else if (key === 'a' || key === 'arrowleft') {
        sendDrive('L');
      } else if (key === 'd' || key === 'arrowright') {
        sendDrive('R');
      } else if (key === ' ') {
        sendDrive('S');
      }
    });

    window.addEventListener('keyup', (e) => {
      const key = e.key.toLowerCase();
      activeKeys.delete(key);

      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
        // If other keys still pressed, resolve priority
        if (activeKeys.has('w') || activeKeys.has('arrowup')) sendDrive('F');
        else if (activeKeys.has('s') || activeKeys.has('arrowdown')) sendDrive('B');
        else if (activeKeys.has('a') || activeKeys.has('arrowleft')) sendDrive('L');
        else if (activeKeys.has('d') || activeKeys.has('arrowright')) sendDrive('R');
        else sendDrive('S');
      }
    });

    // Safety auto-stop on window blur
    window.addEventListener('blur', () => {
      activeKeys.clear();
      sendDrive('S');
    });
  </script>
</body>
</html>
)rawliteral";
