#!/bin/bash
# Healthcheck usando bash /dev/tcp (sem dependências externas)
exec 3<>/dev/tcp/localhost/5000 2>/dev/null
if [ $? -ne 0 ]; then
    exit 1
fi
echo -e "GET /route/v1/driving/-38.5124,-12.9714;-38.51,-12.97?overview=false HTTP/1.0\r\nHost: localhost\r\n\r\n" >&3
read -t 3 response <&3
exec 3>&-
echo "$response" | grep -q "200" && exit 0 || exit 1
