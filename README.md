# DemoForge

**Automated product demo video generator** — turns GitHub repos and websites into polished, narrated demo videos.

## What It Does

```bash
# Analyze a GitHub repo, generate a 2-minute investor pitch, and render to MP4
demoforge generate \
  --repo https://github.com/expressjs/express \
  --audience investors \
  --length 120 \
  --output express-demo.mp4
```

**Result**: Professional demo video with:
- AI-analyzed product features
- Context-aware narration script
- Screenshot captures with smooth transitions
- Natural voice synthesis (Kokoro TTS)
- Subtitles and title cards
- Ken Burns effects and crossfades

## Why DemoForge?

| Feature | DemoForge | Supademo | Navattic | Reprise |
|---------|-----------|----------|----------|---------|
| **Price** | Self-hosted (~$0.10/demo) | $27/mo | $500/mo | $50k+/year |
| **Automation** | Fully automated from repo URL | Manual recording | Manual | Manual |
| **CLI/CI-CD** | ✅ Built for automation | ❌ | ❌ | ❌ |
| **Self-hosted** | ✅ Your infrastructure | ❌ SaaS only | ❌ | ❌ |
| **Code analysis** | ✅ Repomix + Claude | ❌ | ❌ | ❌ |
| **Open source** | ✅ MIT license | ❌ | ❌ | ❌ |

**Perfect for**:
- Cybersecurity companies (keep demos on your infra)
- Developer tools (auto-generate docs videos)
- CI/CD pipelines (generate demos on every release)
- Sales teams (custom demos per prospect)

## Features

### 🤖 AI-Powered Analysis
- Analyzes GitHub repos via Repomix (respects `.gitignore`)
- Scrapes websites with Playwright
- Claude Sonnet 4.5 generates context-aware scripts
- Audience-specific templates (investor, customer, developer, technical)

### 🎙️ Voice Synthesis
- **Kokoro TTS** (primary): 3-11x realtime on CPU, Apache 2.0 license
- **Edge TTS** (fallback): Cloud-based, excellent quality
- **Pocket TTS** (optional): Voice cloning from short samples

### 🎬 Professional Video Assembly
- FFmpeg-based pipeline with xfade transitions
- Ken Burns pan/zoom effects on screenshots
- Automated subtitle generation
- Title cards and lower thirds
- 1080p+ output

### 🌐 Web UI + CLI
- React 19 TypeScript interface
- Real-time progress via Server-Sent Events
- Drag-and-drop scene editor
- Teleprompter mode for manual recording
- CLI for automation and CI/CD

## Quick Start

### Docker (Recommended)

```bash
# Clone and start the stack
git clone https://github.com/horns/demoforge.git
cd demoforge
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

docker compose up -d

# Verify health
curl http://localhost:7500/health

# Generate a demo
docker compose exec app demoforge generate \
  --repo https://github.com/yourusername/yourproject \
  --audience developer \
  --output /app/output/demo.mp4

# Access web UI
open http://localhost:7501
```

### Local Development

```bash
# Requirements: Python 3.12+, Node.js 22+, FFmpeg, git

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up Python environment
uv venv
source .venv/bin/activate
uv sync --all-extras

# Install Playwright browsers
playwright install chromium

# Install repomix globally
npm install -g repomix

# Set up frontend
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173

# In another terminal, start the API server
cd ..
demoforge serve  # Starts on http://localhost:7500
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Docker Compose Stack                        │
├──────────────┬──────────────────────────────────────────┤
│  frontend    │  React 19 + TypeScript + Vite + Tailwind │
│              │  Port 7501 → proxies /api to app:7500   │
├──────────────┼──────────────────────────────────────────┤
│  app         │  FastAPI + Typer CLI                     │
│              │  Playwright + FFmpeg + Kokoro TTS        │
│              │  Claude API (structured outputs)         │
│              │  Port 7500                               │
├──────────────┼──────────────────────────────────────────┤
│  volumes     │  demoforge_output, demoforge_cache       │
└──────────────┴──────────────────────────────────────────┘
```

**Pipeline**: `Analyze → Script → Capture → Voice → Assemble → MP4`

## CLI Reference

```bash
# Analyze a repo/website
demoforge analyze --repo <url>
demoforge analyze --url <website>

# Generate script only
demoforge script --repo <url> --audience investors --length 90

# Full pipeline (analyze + script + capture + voice + assemble)
demoforge generate \
  --repo <url> \
  --audience <investors|customer|developer|technical> \
  --length <seconds> \
  --output <path.mp4>

# Start web server
demoforge serve --host 0.0.0.0 --port 7500
```

## Configuration

### Environment Variables

See `.env.example` for all options. Key variables:

- `ANTHROPIC_API_KEY` — Required for AI analysis and script generation
- `TTS_ENGINE` — `kokoro` (default), `edge`, or `pocket`
- `TTS_VOICE` — Voice ID (see [Voice Options](#voice-options))
- `OUTPUT_DIR` — Where to save rendered videos
- `HEADLESS_BROWSER` — Set to `false` to watch Playwright captures

### YAML Configuration

Alternatively, create `demoforge.yml`:

```yaml
api:
  anthropic_key: sk-ant-...

tts:
  engine: kokoro
  voice: af

output:
  dir: ./output
  max_length: 300

browser:
  headless: true
  timeout: 30000

pipeline:
  enable_caching: true
  parallel_screenshots: 3
```

## Voice Options

### Kokoro TTS (Local, CPU)
- `af` — Female (American, default)
- `am` — Male (American)
- `bf` — Female (British)
- `bm` — Male (British)

### Edge TTS (Cloud)
- `en-US-AriaNeural` — Female (conversational)
- `en-US-GuyNeural` — Male (news anchor)
- `en-GB-SoniaNeural` — Female (British)
- Full list: [Microsoft Edge TTS Voices](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy demoforge/

# Linting
ruff check demoforge/

# Format code
ruff format demoforge/

# Run in Docker with live reload
docker compose up --build
```

## Roadmap

- [x] Core pipeline (analyze, script, capture, voice, assemble)
- [x] CLI interface with Rich progress
- [x] Web UI with SSE progress
- [ ] Voice cloning (Pocket TTS)
- [ ] AI-driven screenshot annotations
- [ ] Hash-based caching
- [ ] GitHub Actions workflow template
- [ ] Video analytics (view tracking)
- [ ] Multi-language support
- [ ] Custom brand templates

## Tech Stack

- **AI**: Claude Sonnet 4.5 (structured outputs)
- **TTS**: Kokoro (primary), Edge TTS (fallback), Pocket TTS (cloning)
- **Browser**: Playwright (screenshots + video capture)
- **Video**: FFmpeg (assembly), Pillow (overlays)
- **Backend**: FastAPI + Typer
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS 4
- **Packaging**: uv + hatchling
- **Container**: Docker + Compose

## License

MIT — see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push and open a Pull Request

## Support

- **Issues**: [GitHub Issues](https://github.com/horns/demoforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/horns/demoforge/discussions)

---

**Built with ❤️ for the developer community**
