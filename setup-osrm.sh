#!/bin/bash
set -euo pipefail

mkdir -p osrm-data

# Baixa só Salvador via Overpass API (retorna XML OSM)
BBOX="-38.55,-13.02,-38.30,-12.80"
URLS=(
  "https://overpass-api.de/api/map?bbox=${BBOX}"
  "https://overpass.kumi.systems/api/map?bbox=${BBOX}"
  "https://overpass.private.coffee/api/map?bbox=${BBOX}"
)

download_ok=0
for url in "${URLS[@]}"; do
  echo "Tentando download via: $url"
  if wget --tries=3 --waitretry=5 -O osrm-data/salvador.osm "$url"; then
    download_ok=1
    break
  fi
done

if [ "$download_ok" -ne 1 ]; then
  echo "Falha ao baixar mapa em todos os endpoints Overpass."
  exit 1
fi

# Processa com o container OSRM (extract -> partition -> customize)
docker run --rm -v $(pwd)/osrm-data:/data \
  ghcr.io/project-osrm/osrm-backend:latest \
  osrm-extract -p /opt/car.lua /data/salvador.osm

docker run --rm -v $(pwd)/osrm-data:/data \
  ghcr.io/project-osrm/osrm-backend:latest \
  osrm-partition /data/salvador.osrm

docker run --rm -v $(pwd)/osrm-data:/data \
  ghcr.io/project-osrm/osrm-backend:latest \
  osrm-customize /data/salvador.osrm
