# ─────────────────────────────────────────────────────
# Stage 1 — Download Nordeste extract & clip to Salvador
# ─────────────────────────────────────────────────────
FROM debian:bookworm-slim AS downloader

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends wget osmium-tool ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Download northeast Brazil from Geofabrik (~500 MB, cached in layer)
RUN wget -q --show-progress -O /tmp/nordeste.osm.pbf \
    "https://download.geofabrik.de/south-america/brazil/nordeste-latest.osm.pbf"

# Clip to Salvador metropolitan area (result ≈ 20-40 MB)
RUN osmium extract \
    --bbox=-38.62,-13.10,-38.28,-12.73 \
    /tmp/nordeste.osm.pbf \
    -o /tmp/salvador.osm.pbf \
    --overwrite && \
    rm /tmp/nordeste.osm.pbf

# ─────────────────────────────────────────────────────
# Stage 2 — OSRM backend
# ─────────────────────────────────────────────────────
FROM osrm/osrm-backend:latest

COPY --from=downloader /tmp/salvador.osm.pbf /data/salvador.osm.pbf
COPY entrypoint.sh /entrypoint.sh
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
