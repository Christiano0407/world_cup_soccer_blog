# ==== Stage: 1 Build ==== #
FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

## === STAGE:2 Nginx production == ##
FROM nginx:1.27-alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /user/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]