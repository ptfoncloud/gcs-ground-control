# Stage 1: Build the Vue 3 application with Vite
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve compiled static files with Nginx
FROM nginx:alpine

# Copy custom Nginx proxy and routing config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production bundle from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]