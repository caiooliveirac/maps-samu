# ── Standalone Dockerfile (para dev local) ──
# Em produção, o build do frontend é feito pelo nginx/Dockerfile (multi-stage)
#
# Uso local:
#   docker build -t maps-samu-frontend .
#   docker run -p 3000:80 maps-samu-frontend

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
