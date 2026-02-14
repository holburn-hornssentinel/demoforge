# =============================================================================
# Multi-stage production Dockerfile for DemoForge
# =============================================================================

# Stage 1: Python Builder - Install Python dependencies
FROM python:3.12-slim AS python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml .python-version ./
COPY README.md ./

# Create virtual environment and install dependencies (no dev deps)
RUN uv venv && \
    . .venv/bin/activate && \
    uv sync --no-dev

# Stage 2: Frontend Builder - Build React app
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build production bundle
RUN npm run build

# Stage 3: Production Runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    # FFmpeg for video assembly
    ffmpeg \
    # espeak-ng for Kokoro TTS
    espeak-ng \
    # Playwright dependencies (minimal set for headless)
    wget \
    ca-certificates \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    # Node.js for repomix
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1001 demoforge && \
    useradd -m -u 1001 -g demoforge demoforge

# Copy Python virtual environment from builder
COPY --from=python-builder --chown=demoforge:demoforge /build/.venv /app/.venv

# Install Playwright browsers (as root, then fix permissions)
RUN . .venv/bin/activate && \
    playwright install chromium && \
    playwright install-deps chromium && \
    chown -R demoforge:demoforge /root/.cache/ms-playwright || true

# Install repomix globally
RUN npm install -g repomix@latest

# Copy application code
COPY --chown=demoforge:demoforge demoforge/ /app/demoforge/
COPY --chown=demoforge:demoforge assets/ /app/assets/

# Copy frontend build
COPY --from=frontend-builder --chown=demoforge:demoforge /build/frontend/dist /app/frontend/dist

# Create output and cache directories
RUN mkdir -p /app/output /app/cache && \
    chown -R demoforge:demoforge /app

# Switch to non-root user
USER demoforge

# Activate venv for all commands
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 7500

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:7500/health || exit 1

# Default command
CMD ["uvicorn", "demoforge.server.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "7500"]
