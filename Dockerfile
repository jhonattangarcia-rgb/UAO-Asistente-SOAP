FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 nodejs npm \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Capa 1: Dependencias Python (rara vez cambian)
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Capa 2: Frontend package.json primero para cachear npm ci
COPY components/webm_recorder/frontend/package.json \
     components/webm_recorder/frontend/package-lock.json* \
     ./components/webm_recorder/frontend/
RUN if [ -f components/webm_recorder/frontend/package.json ]; then \
      cd components/webm_recorder/frontend && \
      npm ci; \
    fi

# Capa 3: Código fuente del frontend + build
COPY components/webm_recorder/frontend/ ./components/webm_recorder/frontend/
RUN if [ -f components/webm_recorder/frontend/package.json ]; then \
      cd components/webm_recorder/frontend && \
      npm run build && \
      rm -rf node_modules; \
    fi

# Capa 4: Código de la app (cambia más seguido)
COPY app.py ./
COPY services/ ./services/
# Capa 5: Usuario no privilegiado
RUN groupadd -r app \
    && useradd -r -g app -d /home/app -m -s /bin/bash app \
    && chown -R app:app /app

ENV HOME=/home/app
USER app

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
