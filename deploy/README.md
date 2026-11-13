# Deploy de Chaco en demo.eibrapp.com.py con Cloudflare Tunnel

Sin reverse proxy (Caddy/nginx): Cloudflare Tunnel expone el contenedor
directamente con HTTPS automático.

## Arquitectura

```
Internet → Cloudflare → cloudflared tunnel → localhost:8010 → Docker (api)
```

## Pasos

### 1. Instalar cloudflared (si no está)

**Windows:**
```powershell
winget install Cloudflare.cloudflared
```

**Linux (Ubuntu/Debian):**
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

### 2. Autenticar con Cloudflare

```bash
cloudflared tunnel login
```
Esto abre el navegador para autorizar. Seleccioná el dominio `eibrapp.com.py`.

### 3. Crear el tunnel

```bash
cloudflared tunnel create chaco-demo
```
Anota el **Tunnel ID** que devuelve (algo como `a1b2c3d4-...`).

### 4. Configurar el DNS en Cloudflare

```bash
cloudflared tunnel route dns chaco-demo demo.eibrapp.com.py
```
Esto crea automáticamente el registro CNAME en Cloudflare.

### 5. Crear el archivo de configuración

Crear `~/.cloudflared/config.yml` (Linux) o `C:\Users\<usuario>\.cloudflared\config.yml` (Windows):

```yaml
tunnel: <TUNNEL_ID>
credentials-file: <ruta_al_json_de_credenciales>

ingress:
  - hostname: demo.eibrapp.com.py
    service: http://localhost:8010
  - service: http_status:404
```

El archivo de credenciales está en `~/.cloudflared/<TUNNEL_ID>.json`.

### 6. Levantar los contenedores de Chaco

```bash
cd /opt/chaco  # o la ruta donde clonaste el repo
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

### 7. Iniciar el tunnel

**Manual (para probar):**
```bash
cloudflared tunnel run chaco-demo
```

**Como servicio (para que arranque con el sistema):**

Linux:
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Windows (PowerShell como admin):
```powershell
cloudflared service install
# Luego iniciar desde Servicios de Windows
```

### 8. Verificar

```bash
curl https://demo.eibrapp.com.py/health
# {"status":"ok","version":"0.1.0"}

curl https://demo.eibrapp.com.py/
# (página web del juego)
```

## Actualizar

```bash
cd /opt/chaco
git pull
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

El tunnel no necesita reiniciarse: sigue apuntando a localhost:8010.

## Notas

- **No necesitás Caddy ni nginx**: Cloudflare Tunnel maneja HTTPS, SSL y enrutamiento.
- **No necesitás abrir puertos en el firewall**: el tunnel es una conexión saliente.
- **La base de datos** se persiste en el volumen `pgdata` de Docker.
- **Ren'Py client**: ya configurado con `API_BASE = "https://demo.eibrapp.com.py"`.
- **CORS**: configurado en `docker-compose.prod.yml` para `https://demo.eibrapp.com.py`.

## Troubleshooting

- Si el tunnel no conecta: verificá que `cloudflared tunnel login` se hizo correctamente.
- Si da 502: verificá que el contenedor de Chaco esté corriendo (`docker compose ps`).
- Si da 404 en assets: verificá que el mount de StaticFiles funciona (el contenedor sirve `/`).
- Logs del tunnel: `cloudflared tunnel info chaco-demo`
