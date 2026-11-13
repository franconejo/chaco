# Deploy de Chaco en demo.eibrapp.com.py

## Requisitos del servidor

- Linux (Ubuntu 22.04+ recomendado) o Windows Server
- Docker + Docker Compose
- Caddy (o nginx) como reverse proxy
- Dominio `demo.eibrapp.com.py` apuntando al servidor (registro A)

## Pasos

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/chaco.git /opt/chaco
cd /opt/chaco
```

### 2. Configurar variables de entorno

Crear `.env` en la raíz:

```
DATABASE_URL=postgresql+psycopg://chaco:CONTRASEÑA_SEGURA@db:5432/chaco
CORS_ORIGINS=["https://demo.eibrapp.com.py"]
```

### 3. Levantar los contenedores

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

### 4. Configurar Caddy

Copiar `deploy/Caddyfile` a `/etc/caddy/Caddyfile` (o agregar el bloque) y recargar:

```bash
sudo caddy reload
```

Caddy obtiene el certificado SSL automáticamente.

### 5. Verificar

```bash
curl https://demo.eibrapp.com.py/health
# {"status":"ok","version":"0.1.0"}

curl https://demo.eibrapp.com.py/
# (página web del juego)
```

### 6. Ren'Py client

El cliente Ren'Py ya está configurado con `API_BASE = "https://demo.eibrapp.com.py"`.
Para distribuirlo, empaquetar la carpeta `renpy/` con Ren'Py (Build → Distribute).

## Notas

- La base de datos se persiste en el volumen `pgdata`. Hacer backup periódico.
- Para actualizar: `git pull && docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build`
- Los retratos son provisorios (rectángulos de color). Reemplazar en `renpy/game/images/` y `web/` cuando haya arte definitivo.
- El puerto 8010 solo escucha en localhost; Caddy es el único que lo expone al exterior.
