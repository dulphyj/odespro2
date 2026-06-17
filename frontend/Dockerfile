FROM node:22-slim AS build

WORKDIR /app
COPY .npmrc package.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build -- --output-path=dist --configuration=production

FROM nginx:1.27-alpine
COPY --from=build /app/dist/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
