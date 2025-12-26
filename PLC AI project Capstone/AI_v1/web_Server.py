# web_server.py
from flask import Flask, jsonify, render_template_string, request
from base_Service import BaseService
from database_Access import DatabaseAccess

# To run, python main.py, python simulate_publisher.py
DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>PLC Device Health Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    :root{
      --bg:#0b1220;
      --panel:#111b2e;
      --panel2:#0f1726;
      --border:#223055;
      --text:#e8eefc;
      --muted:#a9b6d6;
      --muted2:#c6d3f7;      /* brighter for headings */
      --header:#f3f6ff;      /* very visible */
      --accent:#62a7ff;
      --shadow: 0 10px 30px rgba(0,0,0,.35);
      --radius: 16px;
    }

    body{
      background: radial-gradient(1200px 600px at 20% 0%, rgba(98,167,255,.12), transparent 60%),
                  radial-gradient(900px 600px at 90% 20%, rgba(156,99,255,.10), transparent 55%),
                  var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji","Segoe UI Emoji";
    }

    .topbar{
      background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
      border: 1px solid rgba(98,167,255,.18);
      border-radius: 18px;
      padding: 14px 16px;
      box-shadow: var(--shadow);
    }

    .brand{
      font-weight: 700;
      letter-spacing: .2px;
      color: var(--header);
    }

    .sub{
      color: var(--muted);
      font-size: .95rem;
    }

    .pill{
      display:inline-flex;
      align-items:center;
      gap:8px;
      padding:6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.10);
      color: var(--header);
      font-size: .9rem;
    }

    .dot{
      width:10px;height:10px;border-radius:50%;
      background:#27c26c;
      box-shadow: 0 0 0 4px rgba(39,194,108,.12);
    }

    .cardx{
      background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.02));
      border: 1px solid rgba(98,167,255,.14);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .section-title{
      color: var(--header);      /* FIX: visible headings */
      font-weight: 700;
      font-size: 1.05rem;
      letter-spacing: .2px;
      margin: 0;
    }

    .section-meta{
      color: var(--muted);
      font-size: .9rem;
    }

    .table{
      color: var(--text);
      margin-bottom: 0;
    }

    /* FIX: make table headers readable on dark background */
    .table thead th{
      color: var(--header) !important;
      font-weight: 700;
      border-bottom: 1px solid rgba(255,255,255,.18) !important;
      background: rgba(255,255,255,.04);
    }

    .table tbody td{
      border-top: 1px solid rgba(255,255,255,.08);
      vertical-align: middle;
    }

    .site-name{
      color: var(--header);      /* FIX: device name readable */
      font-weight: 700;
    }

    .gateway-muted{
      color: var(--muted2);      /* brighter than muted */
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: .92rem;
    }

    .row-hover:hover{
      background: rgba(98,167,255,.08);
    }

    .row-active{
      background: rgba(98,167,255,.14) !important;
      outline: 1px solid rgba(98,167,255,.25);
    }

    .muted{ color: var(--muted); }
    .muted2{ color: var(--muted2); }

    /* Status badges */
    .badge{
      font-weight: 700;
      letter-spacing: .2px;
      padding: .35rem .55rem;
      border-radius: 999px;
    }
    .badge-Healthy{ background:#1f7a3a; }
    .badge-Warning{ background:#b07a00; }
    .badge-Critical{ background:#9a1b2f; }
    .badge-Unknown{ background:#374151; }

    .metric{
      background: rgba(15,23,38,.55);
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 14px;
      padding: 12px;
      height: 100%;
    }
    .metric .k{
      color: var(--muted2);
      font-size: .85rem;
      margin-bottom: 4px;
    }
    .metric .v{
      color: var(--header);      /* FIX: numbers brighter */
      font-weight: 800;
      font-size: 1.25rem;
      line-height: 1.1;
    }
    .metric .u{
      color: var(--muted);
      font-size: .82rem;
      margin-top: 4px;
    }

    .reason-box{
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 14px;
      padding: 12px;
    }
    .reason-title{
      color: var(--muted2);
      font-size: .85rem;
      margin-bottom: 2px;
    }
    .reason-text{
      color: var(--header);
      font-weight: 750;
      font-size: 1.05rem;
      margin: 0;
    }

    pre{
      background: rgba(15,23,38,.7);
      border: 1px solid rgba(255,255,255,.10);
      padding: 12px;
      border-radius: 14px;
      color: var(--header);
      max-height: 290px;
      overflow: auto;
    }

    .btn-outline-light{
      border-color: rgba(255,255,255,.22);
      color: var(--header);
    }
    .btn-outline-light:hover{
      background: rgba(255,255,255,.10);
      border-color: rgba(255,255,255,.30);
      color: var(--header);
    }

    .searchbar{
      background: rgba(15,23,38,.55);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 12px;
      color: var(--header);
    }
    .searchbar::placeholder{ color: rgba(198,211,247,.65); }
    .searchbar:focus{
      box-shadow: 0 0 0 4px rgba(98,167,255,.16);
      border-color: rgba(98,167,255,.35);
      color: var(--header);
    }

    .tiny{
      font-size: .85rem;
      color: var(--muted);
    }
  </style>
</head>

<body class="p-3 p-md-4">
  <div class="container">

    <!-- Top Bar -->
    <div class="topbar d-flex align-items-center justify-content-between mb-3">
      <div class="d-flex align-items-center gap-3">
        <span class="pill">
          <span class="dot"></span>
          <span>Live · <span id="liveClock">--:--:--</span></span>
        </span>
        <div>
          <div class="brand h4 mb-0">PLC AI-Powered Edge Device Health Check</div>
          <div class="sub">Dashboard reads latest status from DB (auto refresh every 2s)</div>
        </div>
      </div>

      <div class="d-flex align-items-center gap-2">
        <button id="refreshBtn" class="btn btn-outline-light" type="button">Refresh</button>
      </div>
    </div>

    <div class="row g-3">

      <!-- Left: Devices -->
      <div class="col-12 col-lg-7">
        <div class="cardx p-3">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <h5 class="section-title">Devices</h5>
            <div class="section-meta"><span id="deviceCount">0</span> devices</div>
          </div>

          <div class="mb-2">
            <input id="searchInput" class="form-control searchbar" placeholder="Search site or gateway (e.g., PH-NCR-01788 or 142e...)" />
          </div>

          <div class="table-responsive" style="max-height: 560px; overflow:auto;">
            <table class="table table-hover align-middle">
              <thead>
                <tr>
                  <th style="min-width:160px;">Site</th>
                  <th style="min-width:200px;">Gateway</th>
                  <th style="min-width:110px;">Status</th>
                  <th>Reason</th>
                  <th style="min-width:160px;">Updated</th>
                </tr>
              </thead>
              <tbody id="deviceRows"></tbody>
            </table>
          </div>

          <div class="tiny mt-2">Tip: click a row to view details + JSON.</div>
        </div>
      </div>

      <!-- Right: Selected -->
      <div class="col-12 col-lg-5">
        <div class="cardx p-3">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <h5 class="section-title">Selected Device</h5>
            <span id="selectedBadge" class="badge badge-Unknown">Unknown</span>
          </div>

          <div class="muted2 fw-semibold mb-2" id="selectedTitle">Click a device row</div>

          <div class="reason-box mb-3">
            <div class="reason-title">AI Reason</div>
            <p class="reason-text" id="reasonText">-</p>
            <div class="muted mt-1" id="updatedText">Updated: -</div>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <div class="metric">
                <div class="k">Used Memory</div>
                <div class="v" id="usedMem">-</div>
                <div class="u">total - remaining</div>
              </div>
            </div>

            <div class="col-6">
              <div class="metric">
                <div class="k">Used Storage</div>
                <div class="v" id="usedSto">-</div>
                <div class="u">total - remaining</div>
              </div>
            </div>

            <div class="col-6">
              <div class="metric">
                <div class="k">CPU Usage</div>
                <div class="v" id="cpu">-</div>
                <div class="u">%</div>
              </div>
            </div>

            <div class="col-6">
              <div class="metric">
                <div class="k">Temperature</div>
                <div class="v" id="temp">-</div>
                <div class="u">°C (assumed)</div>
              </div>
            </div>
          </div>

          <h6 class="section-title mb-2">Last JSON</h6>
          <pre id="rawJson">{}</pre>
        </div>
      </div>

    </div>
  </div>

<script>
let selectedSite = null;
let lastDevices = [];
let searchTerm = "";

// Badge class helper
function badgeClass(status){
  if(!status) return "badge-Unknown";
  return "badge-" + status;
}

// Clock
function updateClock(){
  const d = new Date();
  document.getElementById("liveClock").innerText = d.toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

async function loadDevices(force=false){
  try{
    const res = await fetch("/api/devices", { cache: "no-store" });
    const data = await res.json();
    lastDevices = data.devices || [];

    // filter
    const filtered = lastDevices.filter(r => {
      const s = (r.siteid || "").toLowerCase();
      const g = (r.gateway || "").toLowerCase();
      const t = searchTerm.toLowerCase().trim();
      if(!t) return true;
      return s.includes(t) || g.includes(t);
    });

    document.getElementById("deviceCount").innerText = filtered.length;

    const tbody = document.getElementById("deviceRows");
    tbody.innerHTML = "";

    filtered.forEach(row => {
      const tr = document.createElement("tr");
      tr.classList.add("row-hover");
      tr.style.cursor = "pointer";
      tr.dataset.siteid = row.siteid || "";

      if(selectedSite && row.siteid === selectedSite){
        tr.classList.add("row-active");
      }

      const status = row.health_status || "Unknown";
      const badge = badgeClass(row.health_status);

      const tsText = row.ts ? new Date(row.ts * 1000).toLocaleString() : "-";

      tr.onclick = () => selectDevice(row.siteid);

      tr.innerHTML = `
        <td class="site-name">${row.siteid || "-"}</td>
        <td class="gateway-muted">${row.gateway || "-"}</td>
        <td><span class="badge ${badge}">${status}</span></td>
        <td class="muted2">${row.reason || "-"}</td>
        <td class="muted">${tsText}</td>
      `;
      tbody.appendChild(tr);
    });

    // keep selection updated
    if(selectedSite){
      await selectDevice(selectedSite, true);
    } else if(filtered.length){
      // optional: auto-select first row on first load
      // await selectDevice(filtered[0].siteid, true);
    }

  } catch(err){
    console.error("loadDevices error:", err);
  }
}

async function selectDevice(siteid, silent=false){
  try{
    selectedSite = siteid;
    const res = await fetch("/api/device?siteid=" + encodeURIComponent(siteid), { cache: "no-store" });
    const data = await res.json();

    const latest = data.latest || {};
    const status = latest.health_status || "Unknown";

    document.getElementById("selectedTitle").innerText = siteid || "—";

    const badge = document.getElementById("selectedBadge");
    badge.className = "badge " + badgeClass(status);
    badge.innerText = status;

    document.getElementById("usedMem").innerText = latest.used_memory ?? "-";
    document.getElementById("usedSto").innerText = latest.used_storage ?? "-";
    document.getElementById("cpu").innerText = latest.cpuusage ?? "-";
    document.getElementById("temp").innerText = latest.temperature ?? "-";

    document.getElementById("reasonText").innerText = latest.reason || "-";
    const ts = latest.ts ? new Date(latest.ts * 1000).toLocaleString() : "-";
    document.getElementById("updatedText").innerText = "Updated: " + ts;

    document.getElementById("rawJson").innerText = JSON.stringify(data.raw_json || {}, null, 2);

    // highlight active row
    document.querySelectorAll("#deviceRows tr").forEach(tr => {
      tr.classList.toggle("row-active", tr.dataset.siteid === selectedSite);
    });

  } catch(err){
    console.error("selectDevice error:", err);
  }
}

// Refresh button FIX (explicitly wire it)
document.getElementById("refreshBtn").addEventListener("click", () => loadDevices(true));

// Search
document.getElementById("searchInput").addEventListener("input", (e) => {
  searchTerm = e.target.value || "";
  loadDevices(true);
});

// Initial load + polling
loadDevices(true);
setInterval(() => loadDevices(false), 2000);
</script>
</body>
</html>
"""

class WebServer(BaseService):
    def __init__(self, db: DatabaseAccess, host: str = "127.0.0.1", port: int = 5000):
        super().__init__("WebServer")
        self.db = db
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._wire_routes()

    def start(self) -> None:
        super().start()
        import threading
        t = threading.Thread(
            target=self.app.run,
            kwargs={"host": self.host, "port": self.port, "debug": False},
            daemon=True
        )
        t.start()
        print(f"[Web] Dashboard running at http://{self.host}:{self.port}")

    def stop(self) -> None:
        super().stop()

    def _wire_routes(self):
        @self.app.get("/")
        def home():
            return render_template_string(DASHBOARD_HTML)

        @self.app.get("/api/devices")
        def api_devices():
            devices = self.db.get_latest_per_device(limit=500)
            out = []
            for d in devices:
                out.append({
                    "ts": d.get("ts"),
                    "gateway": d.get("gateway"),
                    "siteid": d.get("siteid"),
                    "health_status": d.get("health_status"),
                    "reason": d.get("reason")
                })
            return jsonify({"devices": out})

        @self.app.get("/api/device")
        def api_device():
            siteid = request.args.get("siteid", "")
            hist = self.db.get_history(siteid, limit=2000)
            latest = hist[0] if hist else {}
            raw = self.db.get_latest_raw(siteid)
            return jsonify({
                "latest": {
                    "ts": latest.get("ts"),
                    "used_memory": latest.get("used_memory"),
                    "used_storage": latest.get("used_storage"),
                    "cpuusage": latest.get("cpuusage"),
                    "temperature": latest.get("temperature"),
                    "health_status": latest.get("health_status"),
                    "reason": latest.get("reason"),
                },
                "raw_json": raw,
                "history_count": len(hist)
            })
