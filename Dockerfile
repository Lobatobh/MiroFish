# ===== FRONTEND BUILD =====
FROM node:20-alpine AS frontend-build

WORKDIR /app

# Copia o frontend
COPY frontend/ ./frontend/

WORKDIR /app/frontend

# Instala dependências e gera build de produção
RUN npm install
RUN npm run build


# ===== BACKEND =====
FROM python:3.11-slim

WORKDIR /app

# Copia o backend
COPY backend/ ./backend/

# Instala dependências do backend
# PyMuPDF fornece o módulo "fitz" usado para leitura de PDFs
# charset-normalizer e chardet dão suporte à detecção de encoding em TXT/MD
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    gunicorn \
    python-dotenv \
    openai \
    zep-cloud \
    PyMuPDF \
    charset-normalizer \
    chardet

# Copia o frontend compilado para o diretório servido pelo backend
COPY --from=frontend-build /app/frontend/dist /app/backend/dist

WORKDIR /app/backend

# Configuração padrão do Flask
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5001

# Instala curl para healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Verifica se o backend está respondendo
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=20s \
    --retries=3 \
    CMD curl --fail http://localhost:5001/health || exit 1

# Inicializa o MiroFish
CMD [
    "gunicorn",
    "-w", "2",
    "--threads", "4",
    "--timeout", "120",
    "-b", "0.0.0.0:5001",
    "run:create_app()"
]
