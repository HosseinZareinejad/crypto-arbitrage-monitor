@echo off
echo Starting Grafana...
docker run -d --name grafana -p 3000:3000 grafana/grafana
echo Grafana started at http://localhost:3000
echo Default login: admin/admin
