#!/bin/bash
set -e

DATA_DIR="/data"
OSRM_FILE="$DATA_DIR/salvador.osrm"

# ── Process with OSRM if not already done ──
if [ ! -f "${OSRM_FILE}.cell_metrics" ]; then
    echo "============================================"
    echo " Processing OSM data with OSRM..."
    echo "============================================"

    echo "[1/3] Extracting road network..."
    osrm-extract -p /opt/car.lua "$DATA_DIR/salvador.osm.pbf"

    echo "[2/3] Partitioning graph..."
    osrm-partition "$OSRM_FILE"

    echo "[3/3] Customizing weights..."
    osrm-customize "$OSRM_FILE"

    echo "Processing complete."
fi

echo "============================================"
echo " Starting OSRM server on port 5000"
echo "============================================"
exec osrm-routed \
    --algorithm mld \
    --port 5000 \
    --max-table-size 500 \
    "$OSRM_FILE"
