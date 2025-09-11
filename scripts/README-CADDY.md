Local Dev Reverse Proxy with Caddy

Overview
- Serves a public-facing single URL on your LAN (or via a tunnel) that routes:
  - `/api/*` to the Flask backend
  - all other routes to the Vite frontend dev server

Files
- `scripts/Caddyfile`: Caddy v2 config

Usage
1) Export upstreams (adjust IPs/ports for your setup):
   - DietPi backend (Flask): `export BACKEND_UPSTREAM=192.168.1.198:5000`
   - Desktop frontend (Vite): `export FRONTEND_UPSTREAM=192.168.1.237:5173`

2) Run Caddy with the provided config:
   ```bash
   caddy run --config scripts/Caddyfile
   ```

3) Open http://<dietpi-ip>:8080 in your browser. All frontend routes work (SPA), and API traffic is proxied to the backend.

Notes
- This Caddyfile uses plain HTTP on port 8080 for local development. For public HTTPS, put this behind Cloudflare Tunnel or configure a domain and enable Caddy’s automatic HTTPS.
- If you only have the built frontend (no dev server), you can adapt the Caddyfile to serve static files instead:
  ```
  :8080 {
    encode zstd gzip
    handle_path /api/* {
      reverse_proxy 127.0.0.1:5000
    }
    root * /path/to/frontend/dist
    try_files {path} /index.html
    file_server
  }
  ```

