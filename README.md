
# UAO-Asistente-SOAP — Dockerized Instructions

This repository runs locally and provides a Streamlit-based UI for audio/text input and transcription. The following instructions explain how to build and run the project inside a Docker container locally.

## Integración de historial clínico (Supabase)

El módulo "0. Selección de historial clínico" conecta la UI con la base de datos Supabase (tabla `evoluciones_soap`): el médico busca un paciente por ID (ej. `PAC-001`), carga su evolución anterior desde el historial, genera la nueva evolución y la guarda nuevamente en la base —previa ventana de confirmación que recuerda que el contenido es generado por IA y debe validarse—. La vista de resultados muestra los cambios como control de cambios (rojo = eliminado, verde = agregado). Requiere las variables de entorno `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` en `.env` (ver `.env.example`).

Prerequisites

- Docker installed and running on your machine
- Optional: Docker Compose if you prefer compose files
- Optional for local frontend development: Node.js and npm installed locally
- If you want to run the app locally outside Docker, install `ffmpeg`

Build the image

From the repository root (the folder that contains this README and Dockerfile), run:

```
docker build -t uao-asistente-soap:local .
```

Notes:

- This builds the image using the Dockerfile located at `UAO-Asistente-SOAP/Dockerfile`.
- The Dockerfile installs `nodejs` and `npm` and will run `npm ci && npm run build` inside `components/webm_recorder/frontend` if `package.json` is present.
- The image does not include secrets. Provide API keys and other sensitive values at runtime.

Local frontend build

If you are editing the recorder frontend or want to build it locally before running Docker, install Node.js and then run:

```
cd components/webm_recorder/frontend
npm ci
npm run build
```

If you only need to run the app with Docker, local Node.js is not required because the image builds the frontend automatically.

> Note: Docker includes `ffmpeg`, so the image works without local `ffmpeg` installed. Local `ffmpeg` is only needed if you run the Streamlit app outside Docker.
>
> On Windows, install `ffmpeg` with Chocolatey:
>
> ```bash
> choco install ffmpeg -y
> ```

Run the container

Use a detached container with restart policy so it persists across restarts:

```bash
docker run -d --restart unless-stopped -p 8501:8501 -e OPENROUTER_API_KEY="sk-REPLACE_WITH_KEY" -e OPENROUTER_MODEL="openai/whisper-large-v3-turbo" -e API_SECRET_KEY="gsk-REPLACE_WITH_KEY" --name uao-asistente-soap uao-asistente-soap:local
```

If you want to stop the container manually later:

```
docker stop uao-asistente-soap
```

If you want to remove it completely:

```
docker rm uao-asistente-soap
```

If you need to rebuild the image after changes:

```
docker build -t uao-asistente-soap:local .
```

Access the app

Open your browser at http://localhost:8501

Troubleshooting

- If audio processing fails with missing ffmpeg, ensure the container was built successfully and ffmpeg is available. The Dockerfile installs ffmpeg via apt.
- If the app fails to start due to missing Python dependencies, ensure pyproject.toml and uv.lock are present in the project root and the image build completed without errors.
- Secrets and API keys must never be committed in VCS. Use environment variables at runtime.

Quick local development

If you want to keep iterating locally without rebuilding the image every change, continue using quickstart.md (virtualenv flow) and the local Streamlit run command.
