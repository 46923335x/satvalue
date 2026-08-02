FROM python:3.13-slim

WORKDIR /app
COPY . /app

ENV HOST=0.0.0.0
ENV PORT=9000
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:9000/api/health',timeout=3))['ok']"

CMD ["python", "server.py"]
