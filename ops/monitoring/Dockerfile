FROM prom/prometheus:latest
COPY prometheus.yml /etc/opt/monitoring/prometheus.yml
CMD ["--config.file=/etc/opt/monitoring/prometheus.yml", "--web.listen-address=:8001"]