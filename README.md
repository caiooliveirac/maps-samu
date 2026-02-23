# MAPS-SAMU 🚑

**Sistema de Despacho Georreferenciado de Ambulâncias — SAMU 192 Salvador, BA**

Aplicação web para auxiliar plantonistas do SAMU na decisão de qual ambulância despachar para uma ocorrência, baseado em **tempo real de percurso pelas ruas** (OSRM), faixa horária e condições de trânsito.

---

## Início Rápido (Deploy Completo)

```bash
# 1. Clonar repositório
git clone https://github.com/caiooliveirac/maps-samu.git
cd maps-samu

# 2. Criar arquivo de ambiente
cp .env.example .env
# Em produção: alterar POSTGRES_PASSWORD e CORS_ORIGINS

# 3. Subir todos os containers
docker compose up --build -d

# 4. Aguardar todos ficarem healthy (OSRM pode levar ~3-5 min no primeiro build)
docker compose ps
# Todos devem mostrar (healthy)

# 5. Verificar
curl http://localhost/api/health
```

> **ATENÇÃO — Primeiro build do OSRM:** O container OSRM faz download de ~500 MB de dados do Geofabrik (nordeste do Brasil), recorta para Salvador com osmium, e processa com osrm-extract/partition/customize. Isso leva **5-15 minutos** na primeira vez. Nas próximas vezes, o Docker cache e o volume `osrm-data` evitam reprocessamento.

---

## Arquitetura

```
┌───────────────────────────────────────────────────────────────┐
│                       NGINX (porta 80)                        │
│  ┌──────────────────────┐  ┌───────────────────────────────┐  │
│  │  /  → Frontend        │  │  /api/* → Backend (FastAPI)   │  │
│  │  (React 18 + Leaflet) │  │  (upstream :8000)             │  │
│  └──────────────────────┘  └──────────────┬────────────────┘  │
└───────────────────────────────────────────┼────────────────────┘
                                            │
              ┌─────────────────────────────▼──────────────────┐
              │                                                │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐ │
    │ PostgreSQL + PostGIS│              │  OSRM (porta 5000) │ │
    │ (porta 5432 interna)│              │  Routing real       │ │
    └────────────────────┘              └────────────────────┘ │
              │                                                │
              └────────────────────────────────────────────────┘
```

### 4 Containers Docker

| Container | Imagem Base | Porta Interna | Função |
|-----------|-------------|---------------|--------|
| **nginx** | nginx:1.25-alpine | 80 | Proxy reverso + serve SPA (multi-stage: build React → serve) |
| **backend** | python:3.12-slim | 8000 | FastAPI async, lógica de despacho, seed automático |
| **db** | postgis/postgis:16-3.4-alpine | 5432 | PostgreSQL + PostGIS + pg_trgm + unaccent |
| **osrm** | osrm/osrm-backend:latest | 5000 | Routing engine com dados OSM de Salvador |

### Dependências e Health Checks

```
db (healthy) ──┐
               ├──▶ backend (healthy) ──▶ nginx (serve)
osrm (healthy) ┘
```

- **db**: `pg_isready` a cada 5s
- **osrm**: request HTTP `/route/v1/driving/...` a cada 15s, `start_period: 300s` (aguarda processamento inicial)
- **backend**: `GET /api/health` a cada 10s
- **nginx**: só sobe após backend healthy

---

## Estrutura de Pastas

```
maps-samu/
├── docker-compose.yml          # Orquestração dos 4 containers
├── .env.example                # Template de variáveis de ambiente
├── .env                        # Variáveis reais (NÃO versionar)
│
├── nginx/
│   ├── Dockerfile              # Multi-stage: npm build frontend → nginx
│   └── nginx.conf              # /api → backend:8000, / → SPA
│
├── backend/
│   ├── Dockerfile              # Python 3.12, roda seed + uvicorn
│   ├── requirements.txt        # fastapi, sqlalchemy, httpx, etc.
│   └── app/
│       ├── main.py             # Entry point FastAPI (CORS, router)
│       ├── config.py           # Settings via pydantic-settings (.env)
│       ├── database.py         # Async SQLAlchemy engine/session
│       ├── models/models.py    # BaseUnit, Ambulance, Zone, TimeMatrix, Occurrence
│       ├── schemas/dispatch.py # Pydantic request/response DTOs
│       ├── services/
│       │   ├── dispatch.py     # CORE: pipeline de despacho (matriz → OSRM → Haversine)
│       │   ├── osrm.py         # Cliente HTTP para OSRM (route + table API)
│       │   ├── distance.py     # Haversine + estimativas (fallback)
│       │   ├── geocoding.py    # Endereço → coordenadas (Nominatim)
│       │   └── time_period.py  # Detecta faixa horária atual (BRT)
│       ├── seed/
│       │   ├── run.py          # Script idempotente: cria tabelas, popula dados, calcula matriz via OSRM
│       │   ├── bases_data.py   # 10 bases + 12 ambulâncias USA (coordenadas reais)
│       │   └── zones_data.py   # 74 zonas de Salvador com centróides
│       └── api/router.py       # Endpoints: /api/dispatch, /api/bases, /api/health
│
├── frontend/
│   ├── package.json            # React 18, Leaflet, Vite
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx             # Mapa interativo + painel de resultados + captura de coordenadas
│       ├── services/api.js     # Client HTTP (POST /api/dispatch, GET /api/bases)
│       └── styles/global.css   # Dark theme (CARTO dark tiles)
│
├── osrm/
│   ├── Dockerfile              # Multi-stage: Debian (download + osmium clip) → OSRM backend
│   ├── entrypoint.sh           # osrm-extract → partition → customize → routed
│   └── healthcheck.sh          # Bash /dev/tcp healthcheck (sem curl/wget)
│
└── db/
    ├── Dockerfile
    └── init/01-extensions.sql  # CREATE EXTENSION postgis, pg_trgm, unaccent
```

---

## Variáveis de Ambiente (.env)

O arquivo `.env.example` contém todos os valores padrão. Copie para `.env` e ajuste conforme necessário:

```dotenv
# ── PostgreSQL ──
POSTGRES_USER=samu                    # Usuário do banco
POSTGRES_PASSWORD=samu_secure_2024    # ⚠️ ALTERAR EM PRODUÇÃO
POSTGRES_DB=maps_samu                 # Nome do banco
DATABASE_URL=postgresql+asyncpg://samu:samu_secure_2024@db:5432/maps_samu

# ── Backend ──
BACKEND_WORKERS=4                     # Workers uvicorn (usar nº de CPUs)
LOG_LEVEL=info                        # debug | info | warning | error
CORS_ORIGINS=http://localhost,http://localhost:3000

# ── Frontend (build-time) ──
VITE_API_URL=/api                     # Prefixo da API (não alterar)
VITE_MAP_CENTER_LAT=-12.9714          # Centro do mapa (Salvador)
VITE_MAP_CENTER_LNG=-38.5124
VITE_MAP_DEFAULT_ZOOM=12

# ── Serviços internos ──
NOMINATIM_URL=https://nominatim.openstreetmap.org  # Geocoding
OSRM_URL=http://osrm:5000                          # Routing engine (interno)

# ── Timezone ──
TZ=America/Bahia
```

### Variáveis críticas para produção

| Variável | Por que alterar |
|----------|-----------------|
| `POSTGRES_PASSWORD` | Valor padrão é inseguro |
| `CORS_ORIGINS` | Adicionar domínio real do servidor (ex: `https://samu.meudominio.com`) |
| `BACKEND_WORKERS` | Ajustar para número de CPUs disponíveis |
| `DATABASE_URL` | Deve refletir as mesmas credenciais de `POSTGRES_USER`/`POSTGRES_PASSWORD` |

---

## Algoritmo de Despacho

### Pipeline (dispatch.py)

```
Clique no mapa (lat, lng)
    │
    ▼
1. Resolver coordenadas (ou geocodificar endereço via Nominatim)
    │
    ▼
2. Validar que está dentro do bounding box de Salvador
   (lat: -13.02 a -12.80, lng: -38.56 a -38.30)
    │
    ▼
3. Detectar faixa horária atual (timezone America/Bahia)
    │
    ▼
4. Encontrar zona mais próxima (74 zonas, raio máximo 2km)
    │
    ▼
5. Consultar matriz de tempo pré-computada (zona × base × período)
    │                                    │
    ▼ (encontrou)                        ▼ (zona não encontrada)
6. Ranking das 10 bases               7. FALLBACK: OSRM route API para
   ordenado por tempo estimado            cada base → Haversine se OSRM falhar
    │
    ▼
8. Retorna ranking com status de cada ambulância
```

### Cálculo dos Tempos (seed/run.py)

No startup do container, o seed calcula a **matriz completa de tempos** (10 bases × 74 zonas × 5 períodos = **3.700 entradas**):

1. **OSRM Table API** → uma única request calcula toda a matriz 10×74 de tempos free-flow (segundos)
2. **Multiplicadores por faixa horária** aplicados sobre o tempo OSRM:

| Faixa | Horário | Multiplicador | Efeito |
|-------|---------|---------------|--------|
| NORMAL | Seg-Sex 09h-17h | ×1.0 | Baseline OSRM |
| MORNING_RUSH | Seg-Sex 06h-09h | ×1.85 | Trânsito pesado |
| EVENING_RUSH | Seg-Sex 17h-20h | ×1.85 | Trânsito pesado |
| NIGHT | Todos 21h-06h | ×0.70 | Ruas vazias |
| WEEKEND | Sáb-Dom inteiro | ×0.85 | Trânsito leve |

3. **Penalidade de corredor** (+40%) para rotas rush que cruzam eixos congestionados:
   - Av. Paralela, Av. Bonocô/Vasco da Gama, Av. ACM/Tancredo Neves, BR-324, Subúrbio→Centro

4. **Fallback Haversine**: se OSRM estiver indisponível no startup, usa distância em linha reta × fator 1.45 × velocidade média por período

### Cadeia de Fallback (sempre retorna resultado)

```
Matriz pré-computada (OSRM) → OSRM Route API (por ocorrência) → Haversine
```

**Princípio:** o sistema NUNCA retorna vazio. Sempre fornece um ranking, mesmo que aproximado.

---

## Bases do SAMU Salvador

10 bases reais do SAMU 192 Salvador com 12 ambulâncias USA (Unidade de Suporte Avançado):

| Código | Nome | Bairro | Ambulâncias |
|--------|------|--------|-------------|
| BASE-CC | Base Cabula | Cabula | CC70 |
| BASE-PM | Base Pau Miúdo | Pau Miúdo | PM04, PM40 |
| BASE-CZ | Base Cajazeiras | Cajazeiras | CZ50 |
| BASE-PP | Base Periperi | Periperi | PP20 |
| BASE-SM | Base San Martin | San Martin | SM01 |
| BASE-CN | Base Centenário | Centenário | CN10 |
| BASE-BR | Base Boca do Rio | Boca do Rio | BR60, BR05 |
| BASE-IT | Base Itapoã | Itapoã | IT30 |
| BASE-CB | Base Cidade Baixa | Cidade Baixa | CB02 |
| BASE-PR | Base Paralela | Paralela | PR03 |

As coordenadas foram capturadas diretamente nos tiles CARTO/OSM do mapa da aplicação.

---

## OSRM — Routing Engine

O container OSRM fornece tempos de percurso reais pelas ruas de Salvador usando dados OpenStreetMap.

### Como funciona o build

1. **Download**: Geofabrik `nordeste-latest.osm.pbf` (~500 MB)
2. **Clip**: `osmium extract --bbox=-38.62,-13.10,-38.28,-12.73` → extrai apenas Salvador (~30 MB)
3. **Processamento OSRM**: `osrm-extract` → `osrm-partition` → `osrm-customize` (algoritmo MLD)
4. **Serve**: `osrm-routed --algorithm mld --port 5000 --max-table-size 500`

### Cuidados importantes

- O **primeiro build demora** (download de 500 MB + processamento). Docker cache evita rebuild.
- O volume `osrm-data` persiste os dados processados. `docker compose down` (sem `-v`) preserva.
- `docker compose down -v` **apaga** o volume → próximo `up` reprocessa OSRM + refaz seed.
- Se o Geofabrik estiver fora do ar, o build falhará. Alternativa: baixar manualmente o PBF para `osrm/` e ajustar o Dockerfile.
- A bbox do clip cobre a região metropolitana de Salvador. Se precisar expandir, editar o `--bbox` em `osrm/Dockerfile`.

### APIs OSRM usadas

| Endpoint | Uso | Chamado por |
|----------|-----|-------------|
| `GET /route/v1/driving/{lng1},{lat1};{lng2},{lat2}` | Rota ponto-a-ponto | `dispatch.py` (fallback) |
| `GET /table/v1/driving/{coords}?sources=...&destinations=...` | Matriz N×M de tempos | `seed/run.py` (startup) |

---

## API

### POST /api/dispatch (endpoint principal)

```json
// Request — por coordenadas (preferencial, clique no mapa)
{ "latitude": -12.9714, "longitude": -38.5124 }

// Request — por endereço (geocodificado via Nominatim)
{ "address": "Rua da Graça, 100, Salvador" }
```

```json
// Response
{
  "occurrence_lat": -12.9714,
  "occurrence_lng": -38.5124,
  "time_period": "NIGHT",
  "zone_name": "Pelourinho",
  "fallback_used": false,
  "bases_ranked": [
    {
      "rank": 1,
      "base_id": 6,
      "base_code": "BASE-CN",
      "base_name": "Base Centenário",
      "neighborhood": "Centenário",
      "latitude": -12.9908,
      "longitude": -38.5114,
      "estimated_minutes": 3.7,
      "has_available": true,
      "ambulances": [
        {
          "ambulance_id": 7,
          "ambulance_code": "CN10",
          "ambulance_type": "USA",
          "status": "AVAILABLE"
        }
      ]
    }
    // ... 9 bases restantes
  ],
  "total_bases": 10,
  "timestamp": "2026-02-22T20:16:07-03:00"
}
```

### GET /api/bases

Lista todas as bases ativas com suas ambulâncias.

### GET /api/health

```json
{
  "status": "healthy",
  "db": "connected",
  "bases_count": 10,
  "zones_count": 74,
  "matrix_entries": 3700
}
```

### Documentação interativa

- Swagger UI: `http://localhost/api/docs`
- ReDoc: `http://localhost/api/redoc`

---

## Tratamento de Erros

| Cenário | Comportamento | Código |
|---------|---------------|--------|
| Sem coordenadas nem endereço | Erro 400 claro | `MISSING_INPUT` |
| Geocoding falhou | Erro 400 + "clique no mapa" | `GEOCODING_FAILED` |
| Coordenadas fora de Salvador | Erro 400 + perímetro | `OUT_OF_BOUNDS` |
| Zona não encontrada na matriz | Fallback OSRM → Haversine + badge aviso | — |
| OSRM fora do ar no startup | Seed usa Haversine (logs avisam) | — |
| OSRM fora do ar em runtime | Dispatch fallback usa Haversine | — |
| DB fora do ar | Health "degraded" | — |
| Falha ao salvar log de ocorrência | **Não bloqueia** a resposta | — |

---

## Deploy em Servidor (Guia para IA/DevOps)

### Requisitos do servidor

- **Docker** ≥ 24.0 e **Docker Compose** v2 (plugin `docker compose`, não `docker-compose` v1)
- **RAM**: mínimo 2 GB (OSRM + PostgreSQL + Backend)
- **Disco**: mínimo 5 GB livres (imagens Docker + volume PostgreSQL + volume OSRM)
- **CPU**: 2+ cores recomendados (OSRM extract usa CPU intensamente no primeiro build)
- **Porta 80** disponível (ou ajustar em `docker-compose.yml` → `nginx.ports`)
- **Acesso HTTPS ao Geofabrik** durante build do OSRM (download.geofabrik.de)

### Passo a passo em servidor Linux

```bash
# ── 1. Instalar Docker (Ubuntu/Debian) ──
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Fazer logout/login para grupo docker tomar efeito

# ── 2. Clonar e configurar ──
git clone https://github.com/caiooliveirac/maps-samu.git
cd maps-samu
cp .env.example .env

# ── 3. EDITAR .env PARA PRODUÇÃO ──
# OBRIGATÓRIO: trocar POSTGRES_PASSWORD
# OBRIGATÓRIO: ajustar CORS_ORIGINS para o domínio real
# OBRIGATÓRIO: atualizar DATABASE_URL com a nova senha
# OPCIONAL: ajustar BACKEND_WORKERS para nº de CPUs
nano .env

# ── 4. Build e start (primeira vez demora 5-15 min por conta do OSRM) ──
docker compose up --build -d

# ── 5. Acompanhar progresso do OSRM (primeira vez) ──
docker compose logs -f osrm
# Esperar ver: "Starting OSRM server on port 5000"

# ── 6. Verificar que todos estão healthy ──
docker compose ps
# Todos devem estar (healthy)

# ── 7. Testar ──
curl -s http://localhost/api/health | python3 -m json.tool
# Deve retornar: status="healthy", bases_count=10, matrix_entries=3700
```

### Comandos de operação

```bash
# Ver status dos containers
docker compose ps

# Logs de um serviço específico
docker compose logs backend --tail 50
docker compose logs osrm --tail 50

# Reiniciar sem perder dados (preserva volumes)
docker compose restart

# Parar sem perder dados
docker compose down

# ⚠️ Reset completo (APAGA banco + dados OSRM processados)
docker compose down -v
# Próximo "up --build" refaz tudo do zero

# Atualizar código (pull + rebuild)
git pull
docker compose up --build -d
```

### Cuidados críticos

1. **Nunca use `docker compose down -v` em produção** sem intenção — isso apaga o banco de dados e força reprocessamento completo do OSRM.

2. **O seed é idempotente** — se o banco já tem dados, ele não re-insere. Isso significa que alterações em `bases_data.py` ou `zones_data.py` só tomam efeito após `docker compose down -v` (wipe do banco).

3. **OSRM processado fica no volume `osrm-data`** — mesmo após `docker compose down` (sem `-v`), os dados OSRM persistem. O `entrypoint.sh` verifica se já existem arquivos `.cell_metrics` e pula o reprocessamento.

4. **O frontend é built dentro do container nginx** (multi-stage). Alterações em `frontend/src/` exigem `docker compose up --build` para refletir.

5. **Nominatim rate-limit** — o geocoding usa `nominatim.openstreetmap.org` público. Em produção com alto volume, considerar instância local de Nominatim.

6. **Timezone** — todo o cálculo de faixa horária usa `America/Bahia` (UTC-3). Se o servidor estiver em outro fuso, a variável `TZ` no `.env` garante o comportamento correto.

7. **CORS** — em produção, `CORS_ORIGINS` deve conter APENAS os domínios permitidos (não usar `*`).

### Deploy com HTTPS (produção)

Para HTTPS, há duas abordagens:

**Opção A — Reverse proxy externo (recomendado):**
```bash
# Alterar porta no docker-compose.yml de "80:80" para "8080:80"
# Configurar Nginx/Caddy/Traefik no host com certificado SSL
# Proxy pass de https://seudominio.com → http://localhost:8080
```

**Opção B — Certbot no container nginx:**
Requer expor porta 443, montar volume para certificados, e adicionar renovação automática.

### Integração com Nginx existente no host

Se já existe um Nginx no servidor servindo outros sites:

```nginx
# /etc/nginx/sites-available/maps-samu
server {
    listen 443 ssl;
    server_name samu.meudominio.com;

    ssl_certificate /etc/letsencrypt/live/samu.meudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/samu.meudominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;  # Alterar porta do container
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Frontend — Funcionalidades

- **Mapa interativo** com tiles CARTO Dark (`basemaps.cartocdn.com/dark_all`)
- **Clique = despacho** — clique em qualquer ponto de Salvador para consultar ranking
- **Painel de resultados** — mostra ranking das bases, tempos estimados, status das ambulâncias
- **Linhas no mapa** — traça linhas da ocorrência até cada base (cores por ranking)
- **Marcadores de bases** — ícones diferenciados para cada base com tooltip
- **Captura de coordenadas** — modo especial para capturar lat/lng clicando no mapa (botão "Capturar Coordenadas"), com cópia individual ou CSV
- **Geocoding** — campo de endereço com busca por texto (Nominatim)
- **Badge de fallback** — aviso visual quando a estimativa usou Haversine em vez de OSRM

---

## Evolução Futura

- [ ] WebSocket para atualização em tempo real do status das ambulâncias
- [ ] Nominatim local para eliminar dependência de geocoding externo
- [ ] Dashboard de analytics (zonas mais demandadas, tempos médios)
- [ ] Autenticação JWT para plantonistas
- [ ] PWA para uso offline parcial (bases + Haversine)
- [ ] Tráfego real via API (Google/HERE/TomTom) para ajuste dinâmico dos multiplicadores
