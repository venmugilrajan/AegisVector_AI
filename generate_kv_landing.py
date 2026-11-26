import json

with open("landdots.json", "r") as f:
    dots_json = f.read()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AegisVector AI — Uncertainty-Aware Vector Surveillance</title>
  <meta name="description" content="AegisVector AI: Uncertainty-aware dengue outbreak forecasting and resource allocation. Forecasts that know when not to trust themselves.">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" href="https://fonts.gstatic.com/s/anton/v27/1Ptgg87LROyAm3Kz-C8.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="https://fonts.gstatic.com/s/archivo/v25/k3kPo8UDI-1M0wlSV9XAw6lQkqWY8Q82sLydOxI.woff2" as="font" type="font/woff2" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script>document.documentElement.classList.add('js-anim');</script>
  <style>
    :root {{
      --ink: #111111;
      --white: #ffffff;
      --cobalt: #2f63ff;
      --cobalt-hover: #1f4fe0;
      --muted: #5d6270;
      --muted2: #6b6f78;
      --wash: #eef2ff;
      --periwinkle: #a9bcff;
      --giant: #e9e9e9;
      --hairline: #d9dbe0;
      --alert: #e5484d;
      --watch: #f5a524;
      --normal: #059669;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{
      background: var(--white);
      color: var(--ink);
      font-family: 'Archivo', system-ui, -apple-system, sans-serif;
      overflow-x: clip;
      -webkit-font-smoothing: antialiased;
    }}
    body {{
      background: var(--white);
      overflow-x: clip;
      position: relative;
    }}
    a {{ color: inherit; text-decoration: none; }}
    button {{ font: inherit; color: inherit; background: none; border: 0; cursor: pointer; }}

    /* Entrance animation states */
    .js-anim .ent {{ opacity: 0; }}
    .anim-done .ent {{ opacity: 1 !important; }}

    /* Section 1: Hero */
    .hwrap {{
      position: relative;
      width: 100%;
      height: 100vh;
      height: 100svh;
      overflow: hidden;
      background: var(--white);
      z-index: 1;
    }}
    html.sticky .hwrap {{
      height: 165vh;
    }}
    html.sticky section.hero {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 100vh;
      height: 100svh;
      z-index: 1;
      background: var(--white);
    }}
    .gwrap {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}
    #globe {{
      display: block;
      width: 100%;
      height: 100%;
    }}
    .hf {{
      position: absolute;
      left: 0;
      width: calc(1440 * var(--uc, 1px));
      height: calc(900 * var(--uc, 1px));
      pointer-events: none;
      z-index: 2;
    }}
    .hf a, .hf button {{ pointer-events: auto; }}
    
    .logo-box {{
      position: absolute;
      left: calc(40 * var(--uc, 1px));
      top: calc(36 * var(--uc, 1px));
      display: flex;
      align-items: center;
      gap: calc(10 * var(--uc, 1px));
    }}
    .logo-badge {{
      width: calc(32 * var(--uc, 1px));
      height: calc(32 * var(--uc, 1px));
      background: var(--cobalt);
      color: var(--white);
      font-family: 'Anton', sans-serif;
      font-size: calc(18 * var(--uc, 1px));
      display: grid;
      place-items: center;
      border-radius: 6px;
    }}
    .logo-text {{
      font-family: 'Anton', sans-serif;
      font-size: calc(22 * var(--uc, 1px));
      letter-spacing: -0.01em;
      color: var(--ink);
    }}
    
    .vnav {{
      position: absolute;
      left: calc(218 * var(--uc, 1px));
      top: calc(77 * var(--uc, 1px));
      list-style: none;
      display: flex;
      flex-direction: column;
    }}
    .vnav a {{
      font-family: 'JetBrains Mono', monospace;
      font-size: max(calc(13 * var(--uc, 1px)), 11px);
      letter-spacing: 0.09em;
      text-transform: uppercase;
      padding: calc(6.1 * var(--uc, 1px)) 0;
      color: var(--ink);
      transition: color 0.2s;
    }}
    .vnav a:hover {{ color: var(--cobalt); }}

    .copy {{
      position: absolute;
      left: calc(218 * var(--uc, 1px));
      top: calc(294 * var(--uc, 1px));
      width: calc(580 * var(--uc, 1px));
    }}
    .overline {{
      font-family: 'Archivo', sans-serif;
      font-weight: 700;
      font-size: max(calc(19.2 * var(--uc, 1px)), 12px);
      line-height: 1;
      text-transform: uppercase;
      letter-spacing: -0.005em;
      color: var(--cobalt);
    }}
    .hl {{
      margin-top: calc(7 * var(--uc, 1px));
      font-family: 'Anton', "Arial Narrow", sans-serif;
      font-size: calc(114.3 * var(--uc, 1px));
      line-height: 0.953;
      letter-spacing: -0.004em;
      text-transform: uppercase;
      color: var(--ink);
    }}
    .hl .ln {{
      display: block;
      white-space: nowrap;
    }}
    .lede {{
      margin-top: calc(21 * var(--uc, 1px));
      font-size: max(calc(18.2 * var(--uc, 1px)), 13px);
      line-height: 1.45;
      color: var(--muted);
      max-width: max(calc(430 * var(--uc, 1px)), 250px);
    }}
    .btns {{
      margin-top: calc(22 * var(--uc, 1px));
      display: flex;
      gap: calc(15 * var(--uc, 1px));
      flex-wrap: wrap;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: max(calc(42 * var(--uc, 1px)), 36px);
      padding: 0 max(calc(26 * var(--uc, 1px)), 18px);
      border-radius: 999px;
      font-family: 'JetBrains Mono', monospace;
      font-size: max(calc(12 * var(--uc, 1px)), 11px);
      letter-spacing: 0.09em;
      text-transform: uppercase;
      transition: all 0.25s ease;
      cursor: pointer;
    }}
    .btn-primary {{
      background: var(--cobalt);
      color: var(--white);
      border: 1.3px solid var(--cobalt);
      box-shadow: 0 4px 14px rgba(47, 99, 255, 0.28);
    }}
    .btn-primary:hover {{
      background: var(--cobalt-hover);
      border-color: var(--cobalt-hover);
      transform: translateY(-1px);
    }}
    .btn-secondary {{
      background: transparent;
      color: var(--cobalt);
      border: 1.3px solid var(--cobalt);
    }}
    .btn-secondary:hover {{
      background: var(--cobalt);
      color: var(--white);
    }}

    /* Horizon Glow Transition */
    .hz {{
      position: fixed;
      inset: 0;
      z-index: 2;
      pointer-events: none;
      display: none;
    }}

    /* Section 2: Pinned Stats */
    section.stats {{
      position: relative;
      z-index: 3;
      background: transparent;
      width: 100%;
    }}
    .stats .pin {{
      position: sticky;
      top: min(0px, calc(100vh - 900 * var(--us, 1px)));
      height: calc(900 * var(--us, 1px));
      z-index: 1;
      pointer-events: none;
    }}
    .stats .pin a, .stats .pin button {{ pointer-events: auto; }}
    .stats .ph {{
      position: absolute;
      left: calc(64 * var(--us, 1px));
      top: calc(93 * var(--us, 1px));
      width: calc(440 * var(--us, 1px));
      height: calc(236 * var(--us, 1px));
      overflow: hidden;
      background: #1d3b44;
      border-radius: 8px;
    }}
    .stats .ph i {{
      display: block;
      width: 100%;
      height: 100%;
      background: url('https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20261116_131941_31d10ef7-4bff-4a6b-94a7-27e15c950f26.png&w=1200&q=85') 50% 50% / cover no-repeat;
    }}
    .stats h2.big {{
      position: absolute;
      left: calc(64 * var(--us, 1px));
      top: calc(383 * var(--us, 1px));
      font-family: 'Anton', sans-serif;
      font-size: calc(105 * var(--us, 1px));
      line-height: 1;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: var(--ink);
    }}
    .stats h2.big .ln {{
      display: block;
      white-space: nowrap;
    }}

    .stats .col {{
      position: relative;
      margin-top: calc(-900 * var(--us, 1px));
      height: calc((371 + 5 * 166 + 140) * var(--us, 1px));
      z-index: 2;
    }}
    .stats .intro {{
      position: absolute;
      left: calc(594 * var(--us, 1px));
      top: calc(117 * var(--us, 1px));
      width: calc(440 * var(--us, 1px));
      font-size: max(calc(17.9 * var(--us, 1px)), 12.5px);
      line-height: 1.36;
      color: var(--muted2);
    }}
    .stats .intro p + p {{
      margin-top: calc(24 * var(--us, 1px));
    }}
    .stats .intro-links {{
      margin-top: calc(22 * var(--us, 1px));
      display: flex;
      gap: calc(26 * var(--us, 1px));
    }}
    .stats .intro-links a {{
      font-weight: 600;
      color: var(--ink);
      text-decoration: underline 1px;
      text-underline-offset: 0.28em;
      transition: color 0.2s;
    }}
    .stats .intro-links a:hover {{ color: var(--cobalt); }}

    .stats ul.nums {{
      position: absolute;
      left: calc(993 * var(--us, 1px));
      top: calc(371 * var(--us, 1px));
      width: calc(384 * var(--us, 1px));
      list-style: none;
    }}
    .stats ul.nums li {{
      position: relative;
      height: calc(166 * var(--us, 1px));
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .stats ul.nums li:not(:first-child)::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: var(--hairline);
      transform-origin: left;
      transform: scaleX(var(--hl, 1));
    }}
    .stats .n {{
      font-family: 'Anton', sans-serif;
      font-size: calc(82 * var(--us, 1px));
      line-height: 1;
      color: var(--cobalt);
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}
    .stats .c {{
      margin-top: calc(6 * var(--us, 1px));
      font-size: max(calc(17 * var(--us, 1px)), 11.5px);
      color: var(--muted2);
    }}

    /* Section 3: Services Clip Scrub Scene */
    section.track {{
      position: relative;
      z-index: 4;
      background: var(--white);
      width: 100%;
    }}
    .track .scene {{
      position: sticky;
      top: 0;
      height: 100vh;
      height: 100lvh;
      overflow: hidden;
      background: var(--white);
    }}
    .track video {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
      object-fit: cover;
      pointer-events: none;
    }}
    .giant-text {{
      position: absolute;
      font-family: 'Anton', sans-serif;
      font-size: calc(330 * var(--u, 1px));
      line-height: 0.8;
      color: var(--giant);
      white-space: nowrap;
      text-transform: uppercase;
      mix-blend-mode: darken;
      pointer-events: none;
      user-select: none;
    }}
    .speed-readout {{
      position: absolute;
      left: calc(26 * var(--u, 1px));
      top: calc(52 * var(--u, 1px));
      font-family: 'JetBrains Mono', monospace;
      font-size: calc(10.5 * var(--u, 1px));
      letter-spacing: 0.06em;
      color: var(--ink);
      opacity: 0;
      transition: opacity 0.5s;
    }}
    .speed-readout.show {{ opacity: 1; }}

    .services-band {{
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      top: var(--edge-px, 60%);
      background: #111111;
      color: var(--white);
      overflow: hidden;
    }}
    .services-strip {{
      position: absolute;
      top: calc(76 * var(--u, 1px));
      display: flex;
      align-items: flex-start;
      gap: calc(120 * var(--u, 1px));
      will-change: transform;
    }}
    .lead-block {{
      display: flex;
      gap: calc(64 * var(--u, 1px));
      white-space: nowrap;
    }}
    .lead-block h3 {{
      font-family: 'Anton', sans-serif;
      font-size: calc(64 * var(--u, 1px));
      line-height: 0.98;
      text-transform: uppercase;
      color: var(--white);
    }}
    .lead-block h3 span.c-cobalt {{
      color: var(--cobalt);
    }}
    .lead-block .lead-paras {{
      width: calc(250 * var(--u, 1px));
      font-size: calc(12 * var(--u, 1px));
      line-height: 1.5;
      color: rgba(255, 255, 255, 0.62);
      white-space: normal;
    }}
    .lead-block .lead-paras p + p {{
      margin-top: 1em;
    }}

    .card-list {{
      display: flex;
    }}
    .service-card {{
      width: calc(270 * var(--u, 1px));
      padding: 0 calc(30 * var(--u, 1px));
      border-left: 1px solid rgba(255, 255, 255, 0.12);
      flex-shrink: 0;
    }}
    .service-card:first-child {{ border-left: none; }}
    .service-card .icon {{
      width: calc(38 * var(--u, 1px));
      height: calc(38 * var(--u, 1px));
      stroke: var(--white);
      stroke-width: 1.4;
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .service-card h4 {{
      margin-top: calc(22 * var(--u, 1px));
      font-family: 'Anton', sans-serif;
      font-size: calc(26 * var(--u, 1px));
      line-height: 1.05;
      text-transform: uppercase;
      color: var(--white);
    }}
    .service-card p {{
      margin-top: calc(14 * var(--u, 1px));
      font-size: calc(12.4 * var(--u, 1px));
      line-height: 1.5;
      color: rgba(255, 255, 255, 0.65);
    }}

    .services-pill {{
      position: absolute;
      bottom: calc(36 * var(--u, 1px));
      left: 50%;
      transform: translateX(-50%);
      border: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: 999px;
      padding: calc(11 * var(--u, 1px)) calc(22 * var(--u, 1px));
      font-family: 'Archivo', sans-serif;
      font-weight: 500;
      font-size: calc(10 * var(--u, 1px));
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--white);
      opacity: 0;
      transition: opacity 0.6s, transform 0.6s cubic-bezier(0.2, 0.7, 0.2, 1);
    }}
    .services-pill.show {{
      opacity: 1;
    }}
    .services-pill:hover {{
      background: var(--white);
      color: var(--ink);
    }}

    /* Launch Command Center Bar */
    .launch-bar {{
      position: fixed;
      bottom: 24px;
      right: 28px;
      z-index: 100;
      display: flex;
      align-items: center;
      gap: 12px;
      background: rgba(17, 17, 17, 0.88);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      padding: 8px 16px;
      border-radius: 999px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    .launch-bar .pulse-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
      animation: pulse-green 2s infinite;
    }}
    @keyframes pulse-green {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.4); opacity: 0.4; }}
    }}
    .launch-bar span {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #e2e8f0;
      letter-spacing: 0.04em;
    }}
    .launch-bar a {{
      background: var(--cobalt);
      color: var(--white);
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 999px;
      letter-spacing: 0.05em;
      transition: all 0.2s;
    }}
    .launch-bar a:hover {{
      background: var(--cobalt-hover);
      transform: translateY(-1px);
    }}
  </style>
</head>
<body>

  <!-- Data: 3,762 precomputed Land Dots for 3D Globe -->
  <script type="application/json" id="landdots">
{dots_json}
  </script>

  <!-- Live Surveillance Persistent Launch Pill -->
  <div class="launch-bar">
    <div class="pulse-dot"></div>
    <span>SURVEILLANCE BACKEND LIVE</span>
    <a href="/app" id="btn-open-app">OPEN GIS DASHBOARD &rarr;</a>
  </div>

  <!-- SECTION 1: GLOBE HERO -->
  <div class="hwrap">
    <section class="hero" id="top">
      <div class="gwrap">
        <canvas id="globe"></canvas>
      </div>

      <div class="hf">
        <!-- Logo -->
        <a href="#top" class="logo-box ent" id="logo">
          <div class="logo-badge">A</div>
          <div class="logo-text">AegisVector AI</div>
        </a>

        <!-- Vertical Nav -->
        <ul class="vnav ent" id="vnav">
          <li><a href="#about">SYSTEM</a></li>
          <li><a href="#services">CAPABILITIES</a></li>
          <li><a href="/app" style="color:var(--cobalt); font-weight:600;">LIVE MAP &rarr;</a></li>
        </ul>

        <!-- Hero Copy Block -->
        <div class="copy ent" id="copyblock">
          <div class="overline">UNCERTAINTY-AWARE SURVEILLANCE</div>
          <h1 class="hl" id="headline">
            <span class="ln">KNOW WHEN</span>
            <span class="ln">TO TRUST</span>
            <span class="ln">THE FORECAST.</span>
          </h1>
          <p class="lede">
            Dengue outbreak forecasting that computes exact conformal intervals and stays silent when clinical surveillance is too broken to trust.
          </p>
          <div class="btns">
            <a href="/app" class="btn btn-primary">LAUNCH GIS SURVEILLANCE</a>
            <a href="#about" class="btn btn-secondary">SYSTEM BENCHMARKS</a>
          </div>
        </div>
      </div>
    </section>
  </div>

  <!-- Horizon Curved Glow Element -->
  <div class="hz" id="horizonGlow"></div>

  <!-- SECTION 2: STATS & PROBLEM PINNED SCENE -->
  <section class="stats" id="about">
    <div class="pin">
      <div class="ph"><i></i></div>
      <h2 class="big" id="statsHl">
        <span class="ln">PREDICT RISK.</span>
        <span class="ln">GATE ACTION.</span>
        <span class="ln">NEVER BLINDLY</span>
        <span class="ln">DEPLOY TEAMS.</span>
      </h2>
    </div>

    <div class="col">
      <div class="intro">
        <p>
          Traditional epidemic machine learning always forces a point forecast—even when clinical records are corrupted, weeks of data are missing, or reporting lags spike.
        </p>
        <p>
          AegisVector AI couples multi-horizon Quantile XGBoost with split-conformal calibration. When data quality drops, it actively abstains, protecting limited vector control resources from wasteful false alarms.
        </p>
        <div class="intro-links">
          <a href="#services">View operational protocols</a>
          <a href="/app">Enter GIS control room &rarr;</a>
        </div>
      </div>

      <ul class="nums">
        <li>
          <div class="n" data-target="90" data-suffix="%">0%</div>
          <div class="c">Guaranteed Conformal CI Coverage</div>
        </li>
        <li>
          <div class="n" data-target="92.9" data-decimals="1" data-suffix="%">0.0%</div>
          <div class="c">Precision on Confident Wards</div>
        </li>
        <li>
          <div class="n" data-target="3.8" data-decimals="1" data-suffix=" WEEKS">0.0 WEEKS</div>
          <div class="c">Average Lead Time Gained Before Surge</div>
        </li>
        <li>
          <div class="n" data-target="64" data-suffix="%">0%</div>
          <div class="c">Peak Abstention Under 50% Sensor Outage</div>
        </li>
        <li>
          <div class="n">24/7</div>
          <div class="c">Autonomous Quality Scoring & Gated Allocation</div>
        </li>
      </ul>
    </div>
  </section>

  <!-- SECTION 3: VIDEO SCRUB SERVICES / CAPABILITIES SCENE -->
  <section class="track" id="services">
    <div class="scene">
      <video id="servicesVideo" playsinline muted preload="auto" poster="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/2307e4bf-be39-42b4-b579-e168aeccabf0.jpg">
        <source src="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/409763c0-95f4-49d3-a601-dc564d55072b.mp4" type="video/mp4" media="(min-width: 901px)">
        <source src="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/b3718419-7a0a-478d-bfb0-0ff8bef7f3f7.mp4" type="video/mp4">
      </video>

      <div class="giant-text" id="giantLetters">OPERATIONAL PROTOCOLS</div>
      <div class="speed-readout" id="speedReadout">00 KM/H</div>

      <div class="services-band" id="servicesBand">
        <div class="services-strip" id="servicesStrip">
          <div class="lead-block">
            <h3>
              INTELLIGENT<br>
              EPIDEMIOLOGY.<br>
              <span class="c-cobalt">PROVEN PROTECTION.</span>
            </h3>
            <div class="lead-paras">
              <p>
                From district-wide clinical surveillance downscaling to real-time vector response routing, we bring statistical guarantees to municipal outbreak prevention.
              </p>
              <p>
                Confidence is treated as an absolute mathematical gate—not a discount multiplier—ensuring field fumigation teams never deploy on unverified noise.
              </p>
            </div>
          </div>

          <div class="card-list">
            <div class="service-card">
              <svg class="icon" viewBox="0 0 24 24"><path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14"/></svg>
              <h4>DATA QUALITY / SCORING [0,1]</h4>
              <p>Continuous audit of weekly reporting missingness, cluster gaps, and rolling MAD outlier penalties without label leakage.</p>
            </div>

            <div class="service-card">
              <svg class="icon" viewBox="0 0 24 24"><path d="M3 3v18h18M7 16l4-4 4 4 6-6"/></svg>
              <h4>MULTI-HORIZON / QUANTILE ML</h4>
              <p>XGBoost quantile loss across horizons 2, 4, and 6 weeks ahead at the 5th, 50th, and 95th percentiles.</p>
            </div>

            <div class="service-card">
              <svg class="icon" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <h4>SPLIT-CONFORMAL / CALIBRATION</h4>
              <p>Non-parametric interval calibration on held-out temporal sets guaranteeing 90% finite-sample empirical coverage.</p>
            </div>

            <div class="service-card">
              <svg class="icon" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              <h4>BUDGET-GATED / ALLOCATION</h4>
              <p>Priority = MinMax(Risk) x MinMax(Population). Low-confidence wards receive "Verify data first" and are never funded as safe.</p>
            </div>

            <div class="service-card">
              <svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              <h4>3.8 WEEKS / LEAD TIME GAINED</h4>
              <p>Alerts sound weeks prior to epidemic peak, giving municipal agencies time for larviciding and community source reduction.</p>
            </div>
          </div>
        </div>

        <a href="/app" class="services-pill" id="servicesPill">ENTER FULL GIS COMMAND CENTER &rarr;</a>
      </div>
    </div>
  </section>

  <!-- 3D Globe, Horizon Glow, Video Scrubbing & Interactive Engine -->
  <script>
    (function() {{
      const html = document.documentElement;
      let vw = html.clientWidth;
      let vh = html.clientHeight;

      function updateUnits() {{
        vw = html.clientWidth;
        vh = html.clientHeight;
        const uc = Math.min(vw / 1440, vh / 900);
        const uv = Math.max(vw / 1440, vh / 900);
        const us = vw / 1440;
        const u = Math.min(vw / 1440, vh / 960);
        
        html.style.setProperty('--uc', uc + 'px');
        html.style.setProperty('--uv', uv + 'px');
        html.style.setProperty('--us', us + 'px');
        html.style.setProperty('--u', u + 'px');

        if (vw > 900 && vh >= 520) {{
          html.classList.add('sticky');
        }} else {{
          html.classList.remove('sticky');
        }}
      }}
      window.addEventListener('resize', updateUnits);
      updateUnits();

      // ==========================================
      // SECTION 1: 3D DOTTED GLOBE CANVAS ENGINE
      // ==========================================
      const canvas = document.getElementById('globe');
      const ctx = canvas.getContext('2d');
      const dotsData = JSON.parse(document.getElementById('landdots').textContent);
      
      const dots = [];
      for (let i = 0; i < dotsData.length; i += 2) {{
        const lon = (dotsData[i] / 10) * Math.PI / 180;
        const lat = (dotsData[i + 1] / 10) * Math.PI / 180;
        dots.push({{
          x: Math.cos(lat) * Math.sin(lon),
          y: Math.sin(lat),
          z: Math.cos(lat) * Math.cos(lon)
        }});
      }}

      // Cities & Arcs: Colombo (6.93°N, 79.85°E), Singapore (1.35°N, 103.82°E), Rio (22.9°S, 43.17°W)
      const cities = [
        {{ name: 'COLOMBO (EPICENTRE)', lat: 6.93 * Math.PI / 180, lon: 79.85 * Math.PI / 180 }},
        {{ name: 'SINGAPORE', lat: 1.35 * Math.PI / 180, lon: 103.82 * Math.PI / 180 }},
        {{ name: 'RIO DE JANEIRO', lat: -22.9 * Math.PI / 180, lon: -43.17 * Math.PI / 180 }}
      ];

      cities.forEach(c => {{
        c.v = {{
          x: Math.cos(c.lat) * Math.sin(c.lon),
          y: Math.sin(c.lat),
          z: Math.cos(c.lat) * Math.cos(c.lon)
        }};
      }});

      function slerp(v0, v1, t) {{
        let dot = v0.x * v1.x + v0.y * v1.y + v0.z * v1.z;
        dot = Math.max(-1, Math.min(1, dot));
        const theta = Math.acos(dot);
        if (theta < 0.001) return v0;
        const sinT = Math.sin(theta);
        const a = Math.sin((1 - t) * theta) / sinT;
        const b = Math.sin(t * theta) / sinT;
        return {{
          x: a * v0.x + b * v1.x,
          y: a * v0.y + b * v1.y,
          z: a * v0.z + b * v1.z,
          omega: theta
        }};
      }}

      const arcs = [
        {{ from: cities[0], to: cities[1] }},
        {{ from: cities[0], to: cities[2] }}
      ];
      arcs.forEach(a => {{
        a.points = [];
        for (let i = 0; i <= 56; i++) {{
          const t = i / 56;
          const p = slerp(a.from.v, a.to.v, t);
          const lift = 1 + (0.07 + 0.42 * (p.omega / Math.PI)) * Math.sin(Math.PI * t);
          a.points.push({{ x: p.x * lift, y: p.y * lift, z: p.z * lift }});
        }}
      }});

      let startTime = null;
      const tilt = 9 * Math.PI / 180;
      const cosT = Math.cos(tilt);
      const sinT = Math.sin(tilt);

      function resizeCanvas() {{
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = canvas.clientWidth * dpr;
        canvas.height = canvas.clientHeight * dpr;
        ctx.scale(dpr, dpr);
      }}
      window.addEventListener('resize', resizeCanvas);
      resizeCanvas();

      function drawGlobe(time) {{
        if (!startTime) startTime = time;
        const elapsed = (time - startTime) / 1000;

        const cw = canvas.clientWidth;
        const ch = canvas.clientHeight;
        const uv = Math.max(cw / 1440, ch / 900);
        
        ctx.clearRect(0, 0, cw, ch);

        const cx = cw - (1440 - 1166) * uv;
        const cy = ch / 2 + 80 * uv;
        const R = 400 * uv;

        // View longitude
        const viewLon = (-10 - elapsed * 2.4) * Math.PI / 180;
        const cosL = Math.cos(viewLon);
        const sinL = Math.sin(viewLon);

        // 1. Soft Rim Glow
        const haze = ctx.createRadialGradient(cx - 0.05 * R, cy + 0.08 * R, 0.9 * R, cx - 0.05 * R, cy + 0.08 * R, 1.5 * R);
        haze.addColorStop(0, 'rgba(47,99,255,0.48)');
        haze.addColorStop(0.12, 'rgba(90,128,255,0.28)');
        haze.addColorStop(0.4, 'rgba(169,188,255,0.14)');
        haze.addColorStop(1, 'rgba(238,242,255,0)');
        ctx.fillStyle = haze;
        ctx.fillRect(0, 0, cw, ch);

        // 2. Sphere Body
        ctx.save();
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, Math.PI * 2);
        ctx.clip();

        const bodyGrad = ctx.createRadialGradient(cx + 0.3 * R, cy - 0.42 * R, 0.05 * R, cx + 0.1 * R, cy - 0.15 * R, 1.25 * R);
        bodyGrad.addColorStop(0, '#ffffff');
        bodyGrad.addColorStop(0.55, '#f6f8ff');
        bodyGrad.addColorStop(0.85, '#e8eeff');
        bodyGrad.addColorStop(1, '#d5dfff');
        ctx.fillStyle = bodyGrad;
        ctx.fill();

        // Inner Shading
        const innerShade = ctx.createRadialGradient(cx, cy, 0.8 * R, cx, cy, R);
        innerShade.addColorStop(0, 'rgba(47,99,255,0)');
        innerShade.addColorStop(0.75, 'rgba(47,99,255,0.1)');
        innerShade.addColorStop(1, 'rgba(47,99,255,0.42)');
        ctx.fillStyle = innerShade;
        ctx.fill();

        // 3. Draw Land Dots
        for (let i = 0; i < dots.length; i++) {{
          const d = dots[i];
          const rx = d.x * cosL + d.z * sinL;
          const rz = -d.x * sinL + d.z * cosL;
          const ry = d.y * cosT - rz * sinT;
          const fz = d.y * sinT + rz * cosT;

          if (fz > 0.02) {{
            const sx = cx + R * rx;
            const sy = cy - R * ry;
            const rDot = Math.max(0.9, 1.75 * uv) * (0.5 + 0.5 * Math.sqrt(fz));
            const bucket = Math.min(4, Math.floor(fz * 5.5));
            const alpha = 0.22 + bucket * 0.19;

            ctx.fillStyle = `rgba(17,17,17,${{alpha}})`;
            ctx.beginPath();
            ctx.arc(sx, sy, rDot, 0, Math.PI * 2);
            ctx.fill();
          }}
        }}

        // 4. Draw Route Arcs
        arcs.forEach((arc, aIdx) => {{
          const arcProgress = Math.min(1, Math.max(0, (elapsed - 1.0 - aIdx * 0.2) / 1.1));
          if (arcProgress <= 0) return;
          const maxPt = Math.floor(arc.points.length * arcProgress);

          ctx.beginPath();
          let started = false;
          for (let i = 0; i <= maxPt; i++) {{
            const p = arc.points[i];
            const rx = p.x * cosL + p.z * sinL;
            const rz = -p.x * sinL + p.z * cosL;
            const ry = p.y * cosT - rz * sinT;
            const fz = p.y * sinT + rz * cosT;

            if (fz > 0 || (rx * rx + ry * ry > 1)) {{
              const sx = cx + R * rx;
              const sy = cy - R * ry;
              if (!started) {{
                ctx.moveTo(sx, sy);
                started = true;
              }} else {{
                ctx.lineTo(sx, sy);
              }}
            }}
          }}
          ctx.strokeStyle = 'rgba(47,99,255,0.85)';
          ctx.lineWidth = Math.max(1, 1.3 * uv);
          ctx.stroke();
        }});

        // 5. City Pins & Labels
        cities.forEach((c, cIdx) => {{
          const rx = c.v.x * cosL + c.v.z * sinL;
          const rz = -c.v.x * sinL + c.v.z * cosL;
          const ry = c.v.y * cosT - rz * sinT;
          const fz = c.v.y * sinT + rz * cosT;

          const pinProgress = Math.min(1, Math.max(0, (elapsed - 0.8 - cIdx * 0.16) / 0.6));
          if (fz > 0.02 && pinProgress > 0) {{
            const sx = cx + R * rx;
            const sy = cy - R * ry;
            const alpha = Math.min(1, fz * 5) * pinProgress;

            // Pin ring
            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.beginPath();
            ctx.arc(sx, sy, Math.max(3, 4.6 * uv), 0, Math.PI * 2);
            ctx.fillStyle = '#2f63ff';
            ctx.fill();
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();

            // Label
            ctx.font = `500 ${{Math.max(9.5, 12.5 * uv)}}px 'JetBrains Mono', monospace`;
            ctx.textAlign = 'center';
            ctx.fillStyle = '#111111';
            ctx.fillText(c.name, sx, sy - 9 * uv);
            ctx.restore();
          }}
        }});

        ctx.restore(); // Exit clip

        // 6. Outer Rim Highlight
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, Math.PI * 2);
        ctx.lineWidth = Math.max(1, 1.4 * uv);
        ctx.strokeStyle = 'rgba(47,99,255,0.38)';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, R - 0.8, -2.4, -0.3);
        ctx.strokeStyle = 'rgba(255,255,255,0.9)';
        ctx.stroke();

        requestAnimationFrame(drawGlobe);
      }}
      requestAnimationFrame(drawGlobe);

      // ==========================================
      // ENTRANCE ANIMATIONS (Double-Exposure Glitch)
      // ==========================================
      function runGlitch(el, delay) {{
        setTimeout(() => {{
          el.animate([
            {{ opacity: 0, clipPath: 'inset(0 100% 0 0)', transform: 'translateX(-0.05em)', textShadow: '-0.12em 0 0 rgba(47,99,255,0.8), 0.07em 0 0 rgba(17,17,17,0.25)', offset: 0 }},
            {{ opacity: 1, clipPath: 'inset(0 38% 0 0)', transform: 'translateX(0.035em)', textShadow: '0.09em 0 0 rgba(47,99,255,0.65), -0.05em 0 0 rgba(17,17,17,0.3)', offset: 0.3 }},
            {{ opacity: 0.8, clipPath: 'inset(0)', transform: 'translateX(-0.018em)', textShadow: '-0.045em 0 0 rgba(47,99,255,0.55), 0.025em 0 0 rgba(17,17,17,0.2)', offset: 0.55 }},
            {{ opacity: 1, clipPath: 'inset(0)', transform: 'translateX(0.008em)', textShadow: '0.015em 0 0 rgba(47,99,255,0.35), none', offset: 0.78 }},
            {{ opacity: 1, clipPath: 'inset(0)', transform: 'none', textShadow: 'none', offset: 1 }}
          ], {{
            duration: 900,
            easing: 'steps(14, end)',
            fill: 'forwards'
          }}).onfinish = () => el.classList.remove('ent');
        }}, delay);
      }}

      function runFadeUp(el, delay, distance = 14) {{
        setTimeout(() => {{
          el.animate([
            {{ opacity: 0, transform: `translateY(${{distance}}px)` }},
            {{ opacity: 1, transform: 'none' }}
          ], {{
            duration: 800,
            easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)',
            fill: 'forwards'
          }}).onfinish = () => el.classList.remove('ent');
        }}, delay);
      }}

      window.addEventListener('load', () => {{
        runFadeUp(document.getElementById('logo'), 0, 8);
        runFadeUp(document.getElementById('vnav'), 100, 8);
        runFadeUp(document.getElementById('copyblock'), 180, 12);

        const lines = document.querySelectorAll('#headline .ln');
        lines.forEach((ln, idx) => {{
          runGlitch(ln, 260 + idx * 130);
        }});

        setTimeout(() => {{
          html.classList.add('anim-done');
        }}, 4000);
      }});

      // ==========================================
      // SECTION 2 & 3: SCROLL ENGINE & VIDEO SCRUB
      // ==========================================
      const hz = document.getElementById('horizonGlow');
      const video = document.getElementById('servicesVideo');
      const track = document.getElementById('services');
      const giantLetters = document.getElementById('giantLetters');
      const servicesStrip = document.getElementById('servicesStrip');
      const speedReadout = document.getElementById('speedReadout');
      const servicesPill = document.getElementById('servicesPill');

      let lastScrollY = window.scrollY;
      let lastTime = performance.now();
      let smoothedSpeed = 0;

      // IntersectionObserver for Stats count up
      const statElements = document.querySelectorAll('.stats ul.nums li');
      const statsObserver = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
          if (entry.isIntersecting) {{
            const numEl = entry.target.querySelector('.n');
            const target = parseFloat(numEl.getAttribute('data-target'));
            const decimals = parseInt(numEl.getAttribute('data-decimals') || '0');
            const suffix = numEl.getAttribute('data-suffix') || '';

            if (!isNaN(target)) {{
              const startTime = performance.now();
              const duration = 1600;
              function updateCount(now) {{
                const progress = Math.min(1, (now - startTime) / duration);
                const ease = 1 - Math.pow(1 - progress, 3);
                const current = (target * ease).toFixed(decimals);
                numEl.textContent = current + suffix;
                if (progress < 1) requestAnimationFrame(updateCount);
              }}
              requestAnimationFrame(updateCount);
            }}
            statsObserver.unobserve(entry.target);
          }}
        }});
      }}, {{ threshold: 0.2 }});

      statElements.forEach(li => statsObserver.observe(li));

      // Scroll Loop
      function onScroll() {{
        const scrollY = window.scrollY;
        const now = performance.now();
        const dt = Math.max(1, now - lastTime);
        const dy = Math.abs(scrollY - lastScrollY);
        const instantSpeed = (dy / dt) * 1000 / 32;
        smoothedSpeed += (instantSpeed - smoothedSpeed) * 0.1;
        lastScrollY = scrollY;
        lastTime = now;

        // Speed readout
        const clampedSpeed = Math.min(99, Math.round(smoothedSpeed));
        speedReadout.textContent = (clampedSpeed < 10 ? '0' : '') + clampedSpeed + ' KM/H';

        // 1. Horizon Glow Position
        const wrapper = document.querySelector('.hwrap');
        const wrapperHeight = wrapper ? wrapper.offsetHeight : vh;
        const e = (wrapperHeight - scrollY) / vh - 0.47;

        if (e > -0.2 && e < 1.1) {{
          hz.style.display = 'block';
          const drawnEdge = e > 0.12 ? e : -0.03 + 0.15 * Math.exp((e - 0.12) / 0.15);
          const Rx = Math.max(0.75 * vw, 0.9 * vh);
          const Ry = 0.72 * vh;
          const centreY = drawnEdge * vh - Ry;

          hz.style.background = `radial-gradient(${{Rx}}px ${{Ry}}px at 50% ${{centreY}}px,
            rgba(255,255,255,0) 0px,
            rgba(238,242,255,0) ${{Rx * 0.985}}px,
            rgba(214,224,255,0.6) ${{Rx * 1.0}}px,
            #9fb2ff ${{Rx * 1.06}}px,
            #5a80ff ${{Rx * 1.14}}px,
            #2f63ff ${{Rx * 1.236}}px,
            #5a80ff ${{Rx * 1.32}}px,
            #a9bcff ${{Rx * 1.42}}px,
            #dfe6ff ${{Rx * 1.53}}px,
            #ffffff ${{Rx * 1.65}}px)`;
        }} else {{
          hz.style.display = 'none';
        }}

        // 2. Video Scrubbing & Services Scene
        if (track) {{
          const trackTop = track.offsetTop;
          const trackHeight = track.offsetHeight;
          const A = 2.4 * vh;
          const B = 1.8 * vh;

          // Scrub video
          if (video && video.duration) {{
            const q = Math.max(0, Math.min(1, (scrollY - trackTop) / A));
            const targetTime = q * (video.duration - 1/48);
            if (!video.seeking && Math.abs(video.currentTime - targetTime) > 1/60) {{
              video.currentTime = targetTime;
            }}

            if (q >= 0.92) {{
              speedReadout.classList.add('show');
              servicesPill.classList.add('show');
            }} else {{
              speedReadout.classList.remove('show');
              servicesPill.classList.remove('show');
            }}
          }}

          // Horizontal Services Strip & Giant Letters
          const r = Math.max(0, Math.min(1, (scrollY - trackTop - A) / B));
          const stripWidth = servicesStrip ? servicesStrip.scrollWidth : 2000;
          const lettersWidth = giantLetters ? giantLetters.offsetWidth : 1200;

          if (servicesStrip) {{
            const tx = vw - r * (stripWidth + 0.45 * vw);
            servicesStrip.style.transform = `translateX(${{tx}}px)`;
          }}
          if (giantLetters) {{
            const lx = vw - r * (lettersWidth + vw);
            giantLetters.style.transform = `translateX(${{lx}}px)`;
          }}
        }}

        requestAnimationFrame(onScroll);
      }}
      requestAnimationFrame(onScroll);

    }})();
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated index.html with {len(html_content)} bytes")
