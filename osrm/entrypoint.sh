#!/bin/sh
set -eu

DATA_FILE="${OSRM_DATA_FILE:-/data/nordeste.osrm}"
ALGORITHM="${OSRM_ALGORITHM:-mld}"
PORT="${OSRM_PORT:-5000}"
MAX_TABLE_SIZE="${OSRM_MAX_TABLE_SIZE:-500}"

if [ ! -f "$DATA_FILE" ]; then
    echo "ERROR: arquivo OSRM não encontrado: $DATA_FILE"
    echo "Monte os arquivos pré-processados em /data (ex: ./osrm-data:/data)."
    echo "Conteúdo atual de /data:"
    ls -la /data || true
    exit 1
fi

echo "Usando dataset pré-processado: $DATA_FILE"
echo "Subindo osrm-routed (algorithm=$ALGORITHM, port=$PORT)"

exec osrm-routed \
    --algorithm "$ALGORITHM" \
    --port "$PORT" \
    --max-table-size "$MAX_TABLE_SIZE" \
    "$DATA_FILE"
