.PHONY: install test lint format typecheck check run clean help \
        docker-build docker-run docker-stop docker-rm docker-logs docker-rebuild \
        docker-frontend-build check-deps install-ffmpeg

help:
	@echo "-----------------------------------------------"
	@echo "   UAO Asistente SOAP — Comandos Disponibles   "
	@echo "-----------------------------------------------"
	@echo ""
	@echo " INSTALACION"
	@echo "  make install              Instalar dependencias con uv"
	@echo ""
	@echo " CALIDAD"
	@echo "  make lint                 Ejecutar ruff linter"
	@echo "  make format               Formatear codigo con ruff"
	@echo "  make typecheck            Verificar tipos con mypy"
	@echo "  make test                 Ejecutar tests con cobertura"
	@echo "  make check                Ejecutar lint -> typecheck -> test"
	@echo ""
	@echo " EJECUCION"
	@echo "  make run                  Iniciar Streamlit"
	@echo "  make check-deps           Verificar dependencias del sistema"
	@echo "  make install-ffmpeg       Mostrar como instalar ffmpeg"
	@echo ""
	@echo " DOCKER"
	@echo "  make docker-build         Construir imagen Docker"
	@echo "  make docker-run           Iniciar contenedor (detached)"
	@echo "  make docker-stop          Detener contenedor"
	@echo "  make docker-rm            Eliminar contenedor"
	@echo "  make docker-logs          Ver logs del contenedor"
	@echo "  make docker-rebuild       Reconstruir y reiniciar"
	@echo "  make docker-frontend-build  Compilar frontend webm local"
	@echo ""
	@echo " LIMPIEZA"
	@echo "  make clean                Limpiar cache de uv y __pycache__"
	@echo "  make help                 Mostrar esta ayuda"

check-deps:
	@echo "Verificando dependencias del sistema..."
	@ffprobe -version >nul 2>&1 && echo "ffmpeg/ffprobe detectado" || ( \
		echo "ERROR: ffmpeg no encontrado."; \
		echo "Instala ffmpeg segun tu sistema:"; \
		echo "  Windows (Chocolatey): choco install ffmpeg -y"; \
		echo "  Windows (Scoop):      scoop install ffmpeg"; \
		echo "  macOS (Homebrew):     brew install ffmpeg"; \
		echo "  Ubuntu/Debian:        sudo apt install ffmpeg"; \
		exit 1 \
	)

install-ffmpeg:
	@echo "Instala ffmpeg segun tu sistema:"
	@echo "  Windows (Chocolatey): choco install ffmpeg -y"
	@echo "  Windows (Scoop):      scoop install ffmpeg"
	@echo "  macOS (Homebrew):     brew install ffmpeg"
	@echo "  Ubuntu/Debian:        sudo apt install ffmpeg"

install:
	uv sync --extra dev

test:
	uv run pytest tests/ -v --cov=services --cov=app --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

check: lint typecheck test

run: check-deps
	uv run streamlit run app.py

clean:
	uv cache clean
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-build:
	docker build -t uao-asistente-soap:local .

docker-run:
	docker run -d --restart unless-stopped \
		-p 8501:8501 \
		--env-file .env \
		--name uao-asistente-soap \
		uao-asistente-soap:local

docker-stop:
	docker stop uao-asistente-soap

docker-rm:
	docker rm uao-asistente-soap

docker-logs:
	docker logs -f uao-asistente-soap

docker-rebuild: docker-stop docker-rm docker-build docker-run

docker-frontend-build:
	cd components/webm_recorder/frontend && npm ci && npm run build
