FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install --ignore-scripts
COPY . .
RUN rm -rf .angular
RUN npm run build -- --configuration production

FROM nginx:alpine
COPY --from=build /app/dist/docapp-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
