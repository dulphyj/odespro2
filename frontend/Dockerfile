FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build -- --configuration=production

FROM nginx:stable-alpine

COPY --from=builder /app/dist/docapp-frontend/browser /usr/share/nginx/html

EXPOSE 80
