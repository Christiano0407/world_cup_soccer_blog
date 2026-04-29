FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d

EXPOSE 80 443

CMD [ "nginx", "-g", "daemon off;" ]