FROM nginx:1.27-alpine AS production

RUN apk add --no-cache curl

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d

# Remove default.conf that interferes with our config
RUN rm -f /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD [ "nginx", "-g", "daemon off;" ]
