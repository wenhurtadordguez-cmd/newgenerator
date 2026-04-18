# RTLPhishletGenerator v2.0.0

**Automated Evilginx v3 Phishlet Generator for Authorized Red Team Engagements**

> **2026+ Security Edition** - Production-grade, multi-AI providers, enterprise-ready

## 🔒 Security Features

- ✅ **Multi-AI Provider** - Groq, Anthropic, Claude, OpenAI, Azure, Google Gemini with automatic fallback
- ✅ **Complete Phishlet Generation** - No empty fields, ALL form fields captured, complete force_post
- ✅ **Advanced Analysis** - Hidden fields, cookies, auth flows, MFA detection
- ✅ **Security Hardened** - CORS, CSP, input validation, rate limiting, audit logging
- ✅ **Enterprise Ready** - Docker security, resource limits, health checks, graceful shutdown
- ✅ **Modern Stack** - Python 3.12+, React 19, TypeScript 5.8+, latest dependencies

## ⚡ Quick Features

- **Automated URL Analysis** — Playwright-powered browser analysis detects login forms, authentication flows, cookies, ALL involved domains, hidden fields
- **Intelligent Phishlet Generation** — Complete rule-based engine with known platform patterns (Microsoft 365, Google, Okta, GitHub, AWS, and 15+ more)
- **AI Enhancement** — Optional multi-provider LLM integration (Groq, Anthropic, OpenAI, Azure, Google, DeepSeek) via litellm with automatic fallback
- **Complete force_post** — All form fields, search patterns, and value extraction automatically configured
- **Built-in Validation** — Schema validation and cross-section logical checks for Evilginx v3 compatibility
- **YAML Editor** — Full-featured Monaco editor with syntax highlighting
- **Real-time Progress** — WebSocket-based analysis progress with step-by-step feedback
- **Web GUI** — Modern dark-themed interface with wizard workflow

## 📋 Prerequisites

- Python 3.12+ (3.14+ recommended)
- Node.js 20+
- Docker & Docker Compose (optional, recommended)

## 🚀 Quick Start

### Option 1: Docker (Recommended - Secure)

```bash
# Clone or download project
cd RTLPhishletGenerator

# Configure environment
cp .env.example .env

# Add at least ONE AI provider key to .env
# Recommended: Groq (free tier, fast)
# https://console.groq.com/keys
nano .env  # Add GROQ_API_KEY=...

# Start with Docker Compose
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/api/v1/health
```

### Option 2: Manual Setup

```bash
# Backend setup
cd backend
pip install -r requirements.txt
playwright install chromium
cd ..

# Frontend setup
cd frontend
npm install
cd ..

# Run both (requires Make)
make dev

# Or run separately:
# Terminal 1: cd backend && make backend
# Terminal 2: cd frontend && make frontend

# Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

### AI Provider Configuration (at least ONE required)

```env
# Add any/all of these API keys - system auto-fallback
GROQ_API_KEY=gsk_...              # https://console.groq.com
ANTHROPIC_API_KEY=sk-ant-...      # https://console.anthropic.com
OPENAI_API_KEY=sk-...             # https://platform.openai.com
AZURE_API_KEY=...                 # https://azure.microsoft.com
GOOGLE_API_KEY=AIza...            # https://ai.google.dev
DEEPSEEK_API_KEY=sk-...           # https://platform.deepseek.com

# Model and timing
AI_MODEL=groq/mixtral-8x7b-32768  # Primary model
AI_TIMEOUT=60                      # Seconds
AI_MAX_RETRIES=3                   # Auto-retry
```

### Security Configuration

```env
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100            # Per window
RATE_LIMIT_WINDOW=60               # Seconds

# API Authentication (optional)
API_KEY_REQUIRED=false             # Set to true for production
ADMIN_API_KEY=your_secret_key      # If above is true

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Logging
AUDIT_LOGGING_ENABLED=true
LOG_SENSITIVE_DATA=false           # Never log passwords/tokens
```

### Playwright Configuration

```env
PLAYWRIGHT_HEADLESS=true           # Run headless browser
PLAYWRIGHT_TIMEOUT=30000           # Milliseconds
PLAYWRIGHT_VIEWPORT_WIDTH=1920
PLAYWRIGHT_VIEWPORT_HEIGHT=1080
```

## 🎯 Usage

1. **Enter Target URL** — Provide the login page URL (e.g., `https://login.example.com/signin`)
2. **Review Analysis** — Check discovered domains, login forms, cookies, auth flow, **hidden fields**, auth type
3. **Generate Phishlet** — Click "Generate" to produce COMPLETE YAML with force_post fully populated
4. **Edit & Validate** — Fine-tune in Monaco editor, run validation
5. **Export** — Download `.yaml` file for Evilginx

## 🤖 AI Integration & Providers

RTLPhishletGenerator v2.0 uses **litellm** for multi-provider AI support. The system is **provider-agnostic** with automatic fallback:

| Provider | Model | Speed | Quality | Cost | Status |
|----------|-------|-------|---------|------|--------|
| **Groq** | Mixtral 8x7b | ⚡⚡⚡ Fast | Good | Free tier | ✅ Recommended |
| **Anthropic** | Claude 3.5 Sonnet | ⚡⚡ Medium | Excellent | Paid | ✅ Excellent |
| **OpenAI** | GPT-4o | ⚡⚡ Medium | Excellent | Paid | ✅ Popular |
| **Azure OpenAI** | GPT-4o | ⚡⚡ Medium | Excellent | Paid | ✅ Enterprise |
| **Google** | Gemini 2.0 | ⚡⚡⚡ Fast | Good | Free tier | ✅ Fast |
| **DeepSeek** | DeepSeek Chat | ⚡⚡ Medium | Good | Cheap | ✅ Fallback |

**AI Refinement improves phishlet with:**
- Platform-specific cookie/credential knowledge
- Missing subdomain detection
- Cross-domain sub_filter suggestions
- JavaScript injection recommendations for SPA targets
- Hidden field extraction patterns

**Automatic Fallback:**
If configured provider fails, system automatically tries next in chain. No manual intervention needed.

## 📊 Enhanced Phishlet Output

### Complete force_post (NEW!)

```yaml
force_post:
  - path: '/common/login'
    force:
      - key: 'loginfmt'
        get: true
        value: '{{ .username }}'
      - key: 'passwd'
        get: true
        value: '{{ .password }}'
      - key: 'flowToken'
        get: true
        value: ''  # Auto-extracted from response
      - key: 'NONCE'
        get: true
        value: ''  # Auto-extracted
    search:
      - {key: 'loginfmt', search: '(.*)'}
      - {key: 'passwd', search: '(.*)'}
      - {key: 'flowToken', search: '(.*)'}
      - {key: 'NONCE', search: '(.*)'}
    type: 'post'
```

### Complete Analysis Data (NEW!)

```json
{
  "target_url": "https://login.example.com/signin",
  "base_domain": "example.com",
  "discovered_domains": [...],
  "login_forms": [
    {
      "action_url": "...",
      "method": "POST",
      "fields": [
        {"field_name": "email", "field_type": "email", "required": true, "value": null},
        {"field_name": "csrf_token", "field_type": "hidden", "value": "token123"}
      ]
    }
  ],
  "cookies_observed": {"login.example.com": ["sessionid", "auth_token"]},
  "hidden_fields": ["csrf_token", "flowToken", "nonce"],
  "auth_type": "form_based",
  "has_mfa": true,
  "uses_javascript_auth": false
}
```

## 🔐 Security Hardening

### Implemented Protections

- **Input Validation** - All endpoints validate with Pydantic v2
- **Rate Limiting** - slowapi prevents abuse (100 req/min default)
- **CORS Security** - Restricted origins, credentials only from trusted domains
- **HTTP Headers** - CSP, X-Frame-Options, X-Content-Type-Options, HSTS
- **Audit Logging** - All significant operations logged (non-sensitive)
- **Error Handling** - Safe error messages, no info leakage
- **Docker Security** - Non-root user, resource limits, isolation
- **Playwright Isolation** - Sandbox browser, timeout protection

### Security Headers Automatically Added

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | Health check + AI provider status |
| `/api/v1/analyze/` | POST | Analyze target URL |
| `/api/v1/analyze/ws` | WebSocket | Real-time analysis progress |
| `/api/v1/generate/from-url` | POST | Analyze + generate in one call |
| `/api/v1/generate/from-analysis` | POST | Generate from existing analysis |
| `/api/v1/generate/ai-status` | GET | AI providers availability |
| `/api/v1/validate/` | POST | Validate phishlet YAML |

**Full API documentation:** http://localhost:8000/docs (Swagger UI)

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── config.py              # Settings (multi-AI, security)
│   │   ├── routers/               # API endpoints
│   │   │   ├── analyze.py         # URL analysis endpoints
│   │   │   ├── generate.py        # Phishlet generation
│   │   │   ├── validate.py        # YAML validation
│   │   │   └── phishlets.py       # Phishlet library
│   │   ├── services/              # Core business logic
│   │   │   ├── scraper.py         # Playwright website analysis (ENHANCED)
│   │   │   ├── analyzer.py        # Analysis orchestration
│   │   │   ├── generator.py       # Phishlet generation (COMPLETE force_post)
│   │   │   ├── ai_service.py      # Multi-provider LLM integration (NEW)
│   │   │   └── validator.py       # Phishlet validation
│   │   └── schemas/               # Pydantic data models (UPDATED)
│   ├── Dockerfile                 # Security-hardened image
│   └── requirements.txt            # Python dependencies (UPDATED)
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── pages/                 # Page components
│   │   ├── services/              # API client
│   │   ├── store/                 # Zustand state
│   │   └── hooks/                 # Custom hooks
│   ├── Dockerfile                 # Frontend container
│   └── package.json               # Dependencies (UPDATED)
├── docker-compose.yml             # Production stack (SECURITY HARDENED)
├── .env.example                   # Configuration template (UPDATED)
├── SECURITY_UPGRADE_2026.md       # Complete upgrade guide (NEW)
├── Makefile                       # Build/run commands
└── README.md                      # This file
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend type checking
cd frontend
npm run lint

# Security scanning
cd backend
bandit -r app/

# Code linting
ruff check app/
```

## 🐳 Docker Deployment

### Security Features

- **Non-root user** - Runs as `appuser` (UID 1000)
- **Resource limits** - CPU and memory constraints
- **Health checks** - Automatic restart on failure
- **Logging** - Structured JSON logging
- **Isolation** - Network isolation, no capability escalation

### Production Deployment Example

```yaml
# docker-compose.yml (production)
services:
  backend:
    image: rtlphishletgen:2.0.0
    environment:
      DEBUG: 'false'
      RATE_LIMIT_ENABLED: 'true'
      API_KEY_REQUIRED: 'true'
      LOG_SENSITIVE_DATA: 'false'
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📚 Documentation

- **[SECURITY_UPGRADE_2026.md](./SECURITY_UPGRADE_2026.md)** - Complete 2026+ security upgrade guide
- **[Lesson 1: Using RTLPhishletGenerator](docs/lesson-01-using-rtlphishletgenerator.md)** - Step-by-step usage guide
- **[Lesson 2: Creating Phishlets - Techniques](docs/lesson-02-creating-phishlets-manual.md)** - Advanced techniques
- **API Docs** - http://localhost:8000/docs (Swagger UI, interactive)

## 🛠️ Tech Stack

**Backend:**
- Python 3.12+ (latest)
- FastAPI (modern async framework)
- Playwright (browser automation)
- BeautifulSoup4 (HTML parsing)
- Pydantic v2 (data validation)
- litellm (multi-AI provider)
- slowapi (rate limiting)
- ruamel.yaml (YAML handling)

**Frontend:**
- React 19 (latest)
- TypeScript 5.8+ (strict mode)
- Vite 6 (lightning fast builds)
- TailwindCSS 4 (utility framework)
- DOMPurify (XSS prevention)
- TanStack Query (data fetching)
- Zustand (state management)
- Monaco Editor (code editor)

**DevOps:**
- Docker & Docker Compose
- GitHub Actions (CI/CD ready)
- Pre-commit hooks

## ⚠️ Legal Disclaimer

**This tool is provided for authorized security testing purposes ONLY.**

Users must:
1. ✅ Have **written authorization** from the target organization
2. ✅ Operate under a valid **NDA/SOW** for the engagement  
3. ✅ Comply with **all applicable laws** and regulations
4. ✅ NOT use for unauthorized access or malicious purposes

**The developers assume NO liability for misuse of this tool.**

By using RTLPhishletGenerator v2.0, you agree to use it exclusively within the scope of authorized security assessments.

---

## 📞 Support

- **Docs:** [SECURITY_UPGRADE_2026.md](./SECURITY_UPGRADE_2026.md)
- **API Docs:** http://localhost:8000/docs
- **Issues:** Use GitHub Issues for bugs/features (authorized users only)
- **Security:** security@rtlphishletgen.dev (report vulnerabilities responsibly)

---

**Version:** 2.0.0 - Enterprise Edition  
**Release:** 2026  
**Status:** Production-Ready  
**Security Level:** Enterprise-Grade

**Built with ❤️ for authorized red team security testing**
