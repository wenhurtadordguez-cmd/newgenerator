# RTLPhishletGenerator v2.0.0 - Deployment Checklist

## Pre-Deployment ✅

### 1. Code Review
- [ ] All 17 upgrade tasks completed
- [ ] No TODOs or FIXMEs left
- [ ] Code review passed
- [ ] Security scan passed (bandit)

### 2. Dependency Audit
- [ ] Python dependencies updated
- [ ] Node.js dependencies updated
- [ ] No deprecated packages
- [ ] No security vulnerabilities reported

### 3. Configuration
- [ ] .env.example created with all providers
- [ ] README.md updated to v2.0.0
- [ ] SECURITY_UPGRADE_2026.md documentation complete
- [ ] Dockerfile hardened
- [ ] docker-compose.yml secured

## Environment Setup ✅

### Backend Configuration
- [ ] Copy .env.example to .env
- [ ] Add at least ONE AI provider key:
  - [ ] GROQ_API_KEY (recommended - fastest, free tier)
  - [ ] ANTHROPIC_API_KEY
  - [ ] OPENAI_API_KEY
  - [ ] Or any other provider
- [ ] Set DEBUG=false for production
- [ ] Set RATE_LIMIT_ENABLED=true
- [ ] Set AUDIT_LOGGING_ENABLED=true
- [ ] Set LOG_SENSITIVE_DATA=false

### Security Settings
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Optional: Enable API_KEY_REQUIRED=true
- [ ] Optional: Set ADMIN_API_KEY if API auth enabled
- [ ] Verify no hardcoded secrets in code

## Docker Build & Test ✅

### Build Images
```bash
docker-compose build

# Output should show:
# - backend: Complete with non-root user
# - frontend: Complete with security setup
```

**Verify:**
- [ ] Backend image builds successfully
- [ ] Frontend image builds successfully
- [ ] No warnings in build output
- [ ] Image size reasonable (backend ~600MB, frontend ~200MB)

### Start Services
```bash
docker-compose up -d
```

**Verify:**
- [ ] Backend container starts
- [ ] Frontend container starts
- [ ] Both services in healthy state

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Should respond:
{
  "status": "ok",
  "version": "2.0.0",
  "ai_enabled": true,
  "ai_available_providers": ["groq"],  # or your configured provider
  "ai_status": {...}
}

# Frontend availability
curl http://localhost:3000

# Should return HTML
```

**Verify:**
- [ ] Health endpoint responds 200 OK
- [ ] AI providers listed correctly
- [ ] Frontend loads successfully
- [ ] No CORS errors in browser console

## API Testing ✅

### Test Endpoints
```bash
# 1. Health check
curl -X GET http://localhost:8000/api/v1/health

# 2. Get AI status
curl -X GET http://localhost:8000/api/v1/generate/ai-status

# 3. API documentation
curl -X GET http://localhost:8000/docs
```

**Verify:**
- [ ] All endpoints respond
- [ ] No 500 errors
- [ ] No missing dependencies
- [ ] Swagger docs load

### Test Security Headers
```bash
curl -i http://localhost:8000/api/v1/health | grep -E "X-|Content-Security|Strict-Transport"

# Should show:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: ...
```

**Verify:**
- [ ] X-Content-Type-Options present
- [ ] X-Frame-Options present
- [ ] X-XSS-Protection present
- [ ] Strict-Transport-Security present
- [ ] CSP policy present

### Test Rate Limiting
```bash
# Make 101 requests quickly (should get 429 on 101st)
for i in {1..105}; do
  curl -s -w "%{http_code}\n" -o /dev/null http://localhost:8000/api/v1/health
done | sort | uniq -c
```

**Verify:**
- [ ] First 100 requests return 200
- [ ] Request 101+ returns 429 (Too Many Requests)

## Functional Testing ✅

### Create Test Phishlet
1. Open http://localhost:3000
2. Enter test URL: https://login.microsoftonline.com
3. Wait for analysis to complete
4. Verify:
   - [ ] Forms detected
   - [ ] Cookies captured
   - [ ] Auth endpoints identified
   - [ ] Hidden fields extracted

### Generate Phishlet
1. Click "Generate"
2. Wait for AI analysis (should use Groq or configured provider)
3. Verify:
   - [ ] force_post is COMPLETE with all fields
   - [ ] search patterns generated for each field
   - [ ] auth_tokens included
   - [ ] credentials mapped correctly

### Validate Phishlet
1. Click "Validate"
2. Verify:
   - [ ] No validation errors
   - [ ] YAML is well-formed
   - [ ] All required sections present

## Production Deployment ✅

### Pre-Production Checklist
- [ ] All tests passed
- [ ] No console errors
- [ ] No error logs
- [ ] Performance acceptable
- [ ] Health checks passing

### Database/Persistence (if needed)
- [ ] Create data directory: `mkdir -p backend/data/phishlets`
- [ ] Set proper permissions: `chmod 750 backend/data`
- [ ] Verify volume mounted correctly

### Secrets Management
- [ ] .env file is NOT in git
- [ ] .gitignore includes .env
- [ ] .env.example has no real keys
- [ ] Use environment-specific .env files

### Monitoring Setup
- [ ] Configure log aggregation (optional)
- [ ] Set up health check monitoring
- [ ] Configure alerts for failures
- [ ] Monitor AI provider costs

### Backup & Recovery
- [ ] Backup .env file (separately from code)
- [ ] Document recovery procedure
- [ ] Test restore process
- [ ] Document API keys for reference

## Post-Deployment ✅

### Initial Verification
- [ ] Frontend loads at your domain
- [ ] API responds at your API endpoint
- [ ] Health endpoint returns 200
- [ ] All security headers present
- [ ] HTTPS working (if reverse proxy configured)

### User Access
- [ ] Users can access frontend
- [ ] Users can submit URLs for analysis
- [ ] Users can generate phishlets
- [ ] Users can download YAML files

### Monitoring
```bash
# Check container health
docker-compose ps

# Check logs for errors
docker-compose logs backend | grep ERROR
docker-compose logs frontend | tail -20

# Check resource usage
docker stats

# Monitor AI provider usage
docker-compose logs backend | grep "AI"
```

**Verify:**
- [ ] All containers healthy
- [ ] No error messages
- [ ] Resource usage reasonable
- [ ] AI provider being used

### Performance Testing
- [ ] Analysis completes in <15 seconds
- [ ] Phishlet generation in <2 seconds
- [ ] YAML download works
- [ ] No timeout errors

## Maintenance Tasks ✅

### Daily
- [ ] Monitor error logs
- [ ] Check health endpoint
- [ ] Monitor AI provider costs
- [ ] Review rate limit hits

### Weekly
- [ ] Review audit logs
- [ ] Check for security updates
- [ ] Verify backups working
- [ ] Monitor disk space

### Monthly
- [ ] Update dependencies
- [ ] Review security patches
- [ ] Audit user activity
- [ ] Test disaster recovery

## Troubleshooting Checklists ✅

### "No AI providers available"
- [ ] Check .env has at least one API key
- [ ] Verify API key is correct
- [ ] Test AI provider connection:
```bash
curl -X GET http://localhost:8000/api/v1/generate/ai-status
```
- [ ] Check logs for API errors: `docker-compose logs backend | grep -i "ai\|provider"`

### "CORS errors in frontend"
- [ ] Verify CORS_ORIGINS in .env includes your domain
- [ ] Check frontend is making requests to correct API URL
- [ ] Verify security headers are present
- [ ] Check browser console for specific CORS error

### "Rate limit exceeded"
- [ ] Increase RATE_LIMIT_REQUESTS in .env
- [ ] Increase RATE_LIMIT_WINDOW if needed
- [ ] Restart backend: `docker-compose restart backend`

### "Analysis timeout"
- [ ] Increase PLAYWRIGHT_TIMEOUT in .env
- [ ] Check target website is accessible
- [ ] Verify browser automation working
- [ ] Check system resources (CPU, memory)

### "Phishlet validation fails"
- [ ] Check YAML syntax manually
- [ ] Verify all required fields present
- [ ] Run validation endpoint with phishlet JSON
- [ ] Check logs for validation errors

## Security Verification ✅

### Before Production
- [ ] DEBUG=false in .env
- [ ] LOG_SENSITIVE_DATA=false
- [ ] AUDIT_LOGGING_ENABLED=true
- [ ] No API keys in logs
- [ ] HTTPS/SSL configured (if accessible from internet)
- [ ] CORS properly restricted
- [ ] Rate limiting enabled
- [ ] Non-root Docker user confirmed
- [ ] Resource limits set
- [ ] Health checks operational

### SSL/TLS (if publicly accessible)
- [ ] Use reverse proxy (nginx, traefik)
- [ ] Configure Let's Encrypt (certbot)
- [ ] Set Strict-Transport-Security header
- [ ] Redirect HTTP → HTTPS
- [ ] Test SSL with: `curl -I https://your-api/api/v1/health`

### Access Control
- [ ] Firewall rules configured
- [ ] Only necessary ports exposed
- [ ] Rate limiting prevents abuse
- [ ] Audit logs track access
- [ ] Consider IP whitelisting for admin

## Handoff Documentation ✅

### For Operations Team
- [ ] README.md with quick start
- [ ] SECURITY_UPGRADE_2026.md with full details
- [ ] docker-compose.yml explained
- [ ] .env.example with all options
- [ ] Deployment checklist (this file)

### For Security Team
- [ ] SECURITY_UPGRADE_2026.md
- [ ] Threat model
- [ ] Security headers documented
- [ ] Rate limiting configured
- [ ] Audit logging enabled

### For Support Team
- [ ] Troubleshooting guide
- [ ] API documentation
- [ ] Health check instructions
- [ ] Log locations
- [ ] Emergency contact info

## Sign-Off ✅

**Deployment Ready:** [ ] YES [ ] NO

**Deployed By:** ___________________  
**Date:** ___________________  
**Version:** 2.0.0  
**Environment:** Development [ ] Staging [ ] Production [ ]

**Pre-Deployment Review:**
- Code review: [ ] Approved
- Security review: [ ] Approved
- Performance review: [ ] Approved

**Post-Deployment Verification:**
- All tests passing: [ ] YES
- Health checks green: [ ] YES
- Monitoring configured: [ ] YES
- Documentation complete: [ ] YES

---

**Production Deployment Ready!** 🚀

Questions? See:
- README.md
- SECURITY_UPGRADE_2026.md
- ./docs/ directory
