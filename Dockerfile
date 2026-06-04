# Use Python 3.12 slim image based on Debian Bookworm as the base image
FROM python:3.12-slim-bookworm

# Install system dependencies needed for audio processing and frontend build
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy Python project configuration files and install Python deps
COPY pyproject.toml ./
COPY uv.lock ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application files and frontend source
COPY app.py ./
COPY services/ ./services/
COPY components/ ./components/
COPY tmp_audio/ ./tmp_audio/

# Build the recorder frontend if source files are present
RUN if [ -f components/webm_recorder/frontend/package.json ]; then \
      cd components/webm_recorder/frontend && \
      npm ci && \
      npm run build && \
      rm -rf node_modules; \
    fi

# Create an unprivileged user and ensure the application directory is owned by that user.
RUN groupadd -r app \
    && useradd -r -g app -d /home/app -m -s /bin/bash app \
    && chown -R app:app /app

# Set HOME and switch to the unprivileged user for runtime
ENV HOME=/home/app
USER app

# Expose the default Streamlit port
EXPOSE 8501

# Default command to run the Streamlit app
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
