FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM alpine:3.20

COPY --from=build /app/dist/client /dist

# Copies the built SPA into the shared volume, then exits. The nginx
# container mounts the same volume read-only to serve these files.
CMD ["sh", "-c", "rm -rf /site/* && cp -r /dist/. /site/ && echo 'frontend assets deployed'"]
