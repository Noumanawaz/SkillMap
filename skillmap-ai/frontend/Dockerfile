# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the application
RUN npm run build

# Verify build output exists
RUN ls -la /app/dist/ || (echo "Build failed: dist directory not found" && exit 1)
RUN test -f /app/dist/index.html || (echo "Build failed: index.html not found" && exit 1)

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Verify files were copied
RUN ls -la /usr/share/nginx/html/ || (echo "Copy failed: html directory not found" && exit 1)
RUN test -f /usr/share/nginx/html/index.html || (echo "Copy failed: index.html not found" && exit 1)

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

