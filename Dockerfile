# ===== FRONTEND BUILD =====
FROM node:20-alpine as frontend-build

WORKDIR /app
COPY frontend/ ./frontend/

WORKDIR /app/frontend
RUN npm install
RUN npm run build

# ===== BACKEND =====
FROM python:3.11-slim

WORKDIR /app

COPY backend/ ./backend/

RUN pip install --no-cache-dir flask flask-cors gunicorn python-dotenv openai zep-cloud

# Copia frontend buildado
COPY --from=frontend-build /app/frontend/dist /app/backend/dist

WORKDIR /app/backend

ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5001

# Healthcheck
RUN apt-get update && apt-get install -y curl
HEALTHCHECK CMD curl --fail http://localhost:5001/health || exit 1

CMD ["gunicorn", "-w", "2", "--threads", "4", "--timeout", "120", "-b", "0.0.0.0:5001", "run:create_app()"]
