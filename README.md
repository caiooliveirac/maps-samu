# MAPS-SAMU 🚑

**Sistema de Despacho Georreferenciado de Ambulâncias — SAMU Salvador, BA**

Aplicação web para auxiliar plantonistas do SAMU na decisão de qual ambulância despachar para uma ocorrência, baseado em tempo estimado de chegada considerando localização, faixa horária e condições de trânsito.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     NGINX (porta 80)                     │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │  /  → Frontend    │  │  /api/* → Backend (FastAPI)  │ │
│  │  (React + Leaflet)│  │  (upstream :8000)            │ │
│  └──────────────────┘  └──────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   PostgreSQL + PostGIS  │
              │   (porta 5432 interna)  │
              └─────────────────────────┘
```

### Stack

| Camada    | Tecnologia             | Justificativa                            |
|-----------|------------------------|------------------------------------------|
| Frontend  | React 18 + Leaflet     | Mapa interativo, clique = despacho       |
| Backend   | Python FastAPI         | Async, tipado, rápido para I/O           |
| Database  | PostgreSQL 16 + PostGIS| Geoespacial nativo, robusto              |
| Infra     | Docker Compose + Nginx | Containers isolados, proxy reverso       |

### Estrutura de Pastas

```
maps-samu/
├── docker-compose.yml       # Orquestração dos containers
├── .env.example             # Template de variáveis de ambiente
├── nginx/
│   ├── Dockerfile           # Multi-stage: build frontend + serve
│   └── nginx.conf           # Proxy /api → backend, / → frontend
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # Entry point FastAPI
│       ├── config.py        # Settings via env vars
│       ├── database.py      # Async SQLAlchemy engine
│       ├── models/          # SQLAlchemy models
│       ├── schemas/         # Pydantic request/response
│       ├── services/        # Business logic
│       │   ├── dispatch.py  # Core: ranking de bases
│       │   ├── distance.py  # Haversine + estimativas
│       │   ├── geocoding.py # Endereço → coordenadas
│       │   └── time_period.py # Faixa horária atual
│       └── seed/            # Dados iniciais
│           ├── run.py       # Script idempotente
│           ├── bases_data.py    # 10 bases + 12 ambulâncias
│           └── zones_data.py    # ~70 zonas de Salvador
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx          # Componente principal
│       ├── services/api.js  # Client HTTP
│       └── styles/global.css # Dark theme
└── db/
    ├── Dockerfile           # PostGIS 16
    └── init/
        └── 01-extensions.sql # PostGIS + pg_trgm + unaccent
```

---

## Algoritmo de Despacho

### Fluxo Principal
1. Plantonista **clica no mapa** (instantâneo) ou digita endereço
2. Backend identifica a **zona** mais próxima (~70 zonas em Salvador)
3. Consulta a **matriz de tempo pré-computada** para aquela zona × faixa horária
4. Retorna ranking de bases ordenado por tempo estimado de chegada
5. Mostra status de cada ambulância (disponível/despachada/manutenção)

### Matrizes de Tempo

5 faixas horárias com velocidades médias diferentes:

| Faixa           | Horário              | Velocidade Média |
|-----------------|----------------------|------------------|
| NORMAL          | Seg-Sex 09h-17h      | 35 km/h          |
| MORNING_RUSH    | Seg-Sex 06h-09h      | 18 km/h          |
| EVENING_RUSH    | Seg-Sex 17h-20h      | 18 km/h          |
| NIGHT           | Todos 21h-06h        | 50 km/h          |
| WEEKEND         | Sáb-Dom inteiro      | 40 km/h          |

### Corredores de Engarrafamento

Penalidade extra de **1.4x** no rush para rotas que cruzam:
- Av. Paralela (Brotas ↔ Pituba/Imbuí)
- Av. Bonocô (Brotas ↔ Centro)
- Av. ACM (Pituba ↔ Centro/Liberdade)
- BR-324 (Cajazeiras ↔ Cabula/Centro)
- Subúrbio ↔ Centro

### Bairros Grandes Subdivididos

Cajazeiras (I-III, IV-V, VI-VIII, IX-XI), Brotas (Centro, Acupe, Campinas, Engenho Velho), Cabula (Centro, VI, Saboeiro, Pernambués, Narandiba, Tancredo Neves) e Liberdade (Centro, IAPI, Curuzu, Lapinha) são divididos em sub-zonas para que ambulâncias de bases diferentes possam chegar mais rápido a pontos específicos do mesmo bairro.

### Fallback: Haversine

Se a zona não for encontrada na matriz (ponto fora das zonas mapeadas), o sistema usa cálculo Haversine × fator de correção de estrada (1.45 para topografia de Salvador). O usuário é avisado com um badge "estimativa aproximada".

---

## Deploy

### Pré-requisitos
- Docker e Docker Compose instalados
- Porta 80 disponível (ou ajustar no docker-compose)

### Setup Rápido

```bash
# 1. Clonar
git clone https://github.com/caiooliveirac/maps-samu.git
cd maps-samu

# 2. Configurar ambiente
cp .env.example .env
# Editar .env se necessário (senhas, etc)

# 3. Subir tudo
docker compose up --build -d

# 4. Verificar
docker compose ps
curl http://localhost/api/health
```

### Deploy no EC2

```bash
# No EC2 (Amazon Linux 2 ou Ubuntu)
sudo yum install -y docker git   # ou apt install
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone e deploy
git clone https://github.com/caiooliveirac/maps-samu.git
cd maps-samu
cp .env.example .env
# Editar .env com senhas de produção!
docker compose up --build -d
```

### Integração com Nginx existente

Se já tem Nginx rodando no EC2 para outra aplicação, adicione um upstream:

```nginx
# No nginx.conf do host
upstream maps_samu {
    server 127.0.0.1:8081;  # Mudar porta no docker-compose
}

server {
    location /samu/ {
        proxy_pass http://maps_samu/;
    }
}
```

---

## Bases do SAMU Salvador

| Código  | Nome                    | Bairro      | Ambulâncias |
|---------|-------------------------|-------------|-------------|
| BASE-01 | Base Central - Brotas   | Brotas      | 2 (USB+USA) |
| BASE-02 | Base Itapagipe          | Itapagipe   | 1 (USB)     |
| BASE-03 | Base Cabula             | Cabula      | 1 (USB)     |
| BASE-04 | Base Pituba             | Pituba      | 2 (USB+USA) |
| BASE-05 | Base Itapuã             | Itapuã      | 1 (USB)     |
| BASE-06 | Base Pau da Lima        | Pau da Lima | 1 (USB)     |
| BASE-07 | Base Cajazeiras         | Cajazeiras  | 1 (USB)     |
| BASE-08 | Base Subúrbio           | Periperi    | 1 (USB)     |
| BASE-09 | Base Barra              | Barra       | 1 (USB)     |
| BASE-10 | Base Liberdade          | Liberdade   | 1 (USA)     |

**USB** = Unidade de Suporte Básico | **USA** = Unidade de Suporte Avançado

---

## API

### POST /api/dispatch

```json
// Request (por coordenadas — preferencial)
{ "latitude": -12.9714, "longitude": -38.5124 }

// Request (por endereço)
{ "address": "Rua da Graça, 100, Salvador" }

// Response
{
  "occurrence_lat": -12.9714,
  "occurrence_lng": -38.5124,
  "time_period": "MORNING_RUSH",
  "zone_name": "Pelourinho",
  "fallback_used": false,
  "bases_ranked": [
    {
      "rank": 1,
      "base_id": 10,
      "base_code": "BASE-10",
      "base_name": "Base Liberdade",
      "estimated_minutes": 5.2,
      "has_available": true,
      "ambulances": [...]
    }
  ]
}
```

### GET /api/bases
Lista todas as bases com ambulâncias.

### GET /api/health
Health check com contagem de bases, zonas e entradas na matriz.

---

## Tratamento de Erros

| Cenário | Comportamento | Código |
|---------|---------------|--------|
| Sem coordenadas nem endereço | Erro 400 claro | MISSING_INPUT |
| Geocoding falhou (timeout/not found) | Erro 400 + "clique no mapa" | GEOCODING_FAILED |
| Coordenadas fora de Salvador | Erro 400 + perímetro | OUT_OF_BOUNDS |
| Zona não encontrada na matriz | **Fallback Haversine** + aviso | — |
| DB fora do ar | Health degraded, último ranking em cache | — |
| Falha ao salvar log de ocorrência | **Não bloqueia resposta** | — |

**Princípio:** o sistema NUNCA retorna vazio. Sempre fornece um ranking, mesmo que aproximado.

---

## Evolução Futura

- [ ] OSRM self-hosted para tempos reais de rota
- [ ] WebSocket para atualização em tempo real do status das ambulâncias
- [ ] Nominatim local para eliminar dependência de geocoding externo
- [ ] Dashboard de analytics (zonas mais demandadas, tempos médios)
- [ ] Autenticação JWT para plantonistas
- [ ] PWA para uso offline parcial (bases + Haversine)
