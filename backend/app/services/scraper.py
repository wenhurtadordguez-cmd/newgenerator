import re
import logging
from typing import Optional, Callable, Awaitable
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Page, Request, Response
from bs4 import BeautifulSoup

from app.schemas.analysis import LoginFormField, LoginFormInfo, DiscoveredDomain
from app.config import settings

logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self):
        self.redirect_chain: list[str] = []
        self.network_requests: list[dict] = []
        self.cookies_by_domain: dict[str, list[str]] = {}
        self.domains_seen: set[str] = set()
        self.auth_endpoints: list[str] = []
        self.hidden_fields: list[str] = []

    async def analyze_url(
        self,
        url: str,
        callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> dict:
        """Complete URL analysis with all form fields, cookies, and endpoints captured"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=settings.playwright_headless)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={
                    "width": settings.playwright_viewport_width,
                    "height": settings.playwright_viewport_height,
                },
                ignore_https_errors=True,
            )

            page = await context.new_page()
            page.on("request", self._on_request)
            page.on("response", self._on_response)

            try:
                # Step 1: Navigate
                if callback:
                    await callback("Navigating to target URL...")
                await page.goto(url, wait_until="networkidle", timeout=settings.playwright_timeout)
                await page.wait_for_timeout(3000)

                # Step 2: Extract page content
                if callback:
                    await callback("Extracting page content...")
                html_content = await page.content()
                page_title = await page.title()
                self._extract_domains_from_js(html_content)

                # Step 3: Detect login forms (with hidden fields)
                if callback:
                    await callback("Detecting login forms and hidden fields...")
                login_forms = await self._detect_login_forms(page, html_content, url)

                # Step 4: Capture all cookies
                if callback:
                    await callback("Capturing all cookies...")
                cookies = await context.cookies()
                for cookie in cookies:
                    domain = cookie["domain"]
                    if domain not in self.cookies_by_domain:
                        self.cookies_by_domain[domain] = []
                    if cookie["name"] not in self.cookies_by_domain[domain]:
                        self.cookies_by_domain[domain].append(cookie["name"])

                # Step 5: Identify all auth endpoints
                if callback:
                    await callback("Identifying authentication endpoints...")
                self._classify_auth_endpoints()

                # Step 6: Build domain map
                if callback:
                    await callback("Building domain map...")
                discovered_domains = self._build_domain_map(url)

                # Step 7: Detect post-login, MFA, JS auth
                if callback:
                    await callback("Detecting authentication mechanisms...")
                post_login_url = self._detect_post_login_url()
                has_mfa = self._detect_mfa_indicators(html_content)
                uses_js_auth = self._detect_js_auth(html_content)
                auth_type = self._detect_auth_type(html_content, login_forms)

                parsed = urlparse(url)
                return {
                    "target_url": url,
                    "base_domain": parsed.netloc,
                    "discovered_domains": discovered_domains,
                    "login_forms": login_forms,
                    "cookies_observed": self.cookies_by_domain,
                    "redirect_chain": self.redirect_chain,
                    "post_login_url": post_login_url,
                    "login_path": parsed.path or "/",
                    "has_mfa": has_mfa,
                    "uses_javascript_auth": uses_js_auth,
                    "auth_api_endpoints": self.auth_endpoints,
                    "page_title": page_title,
                    "network_requests": self.network_requests,
                    "html_content": html_content,
                    "hidden_fields": self.hidden_fields,
                    "auth_type": auth_type,
                }
            finally:
                await browser.close()

    def _on_request(self, request: Request):
        """Track all requests made by the page"""
        parsed = urlparse(request.url)
        if parsed.netloc:
            self.domains_seen.add(parsed.netloc)
        self.network_requests.append({
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
        })
        if request.is_navigation_request():
            self.redirect_chain.append(request.url)

    def _on_response(self, response: Response):
        """Track cookies from response headers"""
        headers = response.headers
        set_cookie = headers.get("set-cookie", "")
        if set_cookie:
            parsed = urlparse(response.url)
            domain = parsed.netloc
            # Handle multiple Set-Cookie headers
            for cookie_header in headers.getlist("set-cookie") if hasattr(headers, 'getlist') else [set_cookie]:
                cookie_names = re.findall(r"^([^=]+)=", cookie_header, re.MULTILINE)
                if domain not in self.cookies_by_domain:
                    self.cookies_by_domain[domain] = []
                for name in cookie_names:
                    name = name.strip()
                    if name and name not in self.cookies_by_domain[domain]:
                        self.cookies_by_domain[domain].append(name)

    async def _detect_login_forms(
        self, page: Page, html: str, base_url: str
    ) -> list[LoginFormInfo]:
        """Detect login forms with complete field extraction including hidden fields"""
        soup = BeautifulSoup(html, "html.parser")
        forms: list[LoginFormInfo] = []

        # Find all forms with password inputs
        for form_idx, form in enumerate(soup.find_all("form")):
            password_inputs = form.find_all("input", {"type": "password"})
            if not password_inputs:
                continue

            action = form.get("action", "")
            if action and not action.startswith("http"):
                action = urljoin(base_url, action)

            fields: list[LoginFormField] = []
            
            # Extract ALL input fields (visible and hidden)
            for inp in form.find_all("input"):
                input_type = inp.get("type", "text")
                field_name = inp.get("name", "")
                
                # Skip submit/reset buttons
                if input_type in ("submit", "reset", "button"):
                    continue
                
                # Track hidden fields
                if input_type == "hidden":
                    self.hidden_fields.append(field_name)

                # Skip empty names
                if not field_name:
                    continue

                # Get label information
                label_text = None
                field_id = inp.get("id")
                if field_id:
                    label_el = soup.find("label", attrs={"for": field_id})
                    if label_el:
                        label_text = label_el.get_text(strip=True)
                if not label_text:
                    label = inp.find_previous("label")
                    if label:
                        label_text = label.get_text(strip=True)

                fields.append(LoginFormField(
                    field_name=field_name,
                    field_type=input_type,
                    field_id=field_id,
                    placeholder=inp.get("placeholder"),
                    label=label_text,
                    value=inp.get("value"),  # Capture default values
                    required=inp.has_attr("required"),
                ))

            # Get submit button text
            submit = form.find("button", {"type": "submit"}) or form.find("input", {"type": "submit"})
            submit_text = None
            if submit:
                submit_text = submit.get_text(strip=True) or submit.get("value", "")

            if fields:  # Only add if fields were found
                forms.append(LoginFormInfo(
                    action_url=action or base_url,
                    method=form.get("method", "POST").upper(),
                    fields=fields,
                    submit_button_text=submit_text,
                    id=form.get("id"),
                    name=form.get("name"),
                ))

        # Strategy 2: Playwright for SPA login forms (if no forms found via HTML)
        if not forms:
            try:
                password_field = await page.query_selector(
                    'input[type="password"], input[name*="pass"], input[name*="pwd"]'
                )
                if password_field:
                    email_field = await page.query_selector(
                        'input[type="email"], input[name*="email"], '
                        'input[name*="user"], input[name*="login"]'
                    )
                    fields = []
                    if email_field:
                        fields.append(LoginFormField(
                            field_name=await email_field.get_attribute("name") or "email",
                            field_type=await email_field.get_attribute("type") or "email",
                            field_id=await email_field.get_attribute("id"),
                            placeholder=await email_field.get_attribute("placeholder"),
                        ))
                    fields.append(LoginFormField(
                        field_name=await password_field.get_attribute("name") or "password",
                        field_type="password",
                        field_id=await password_field.get_attribute("id"),
                        placeholder=await password_field.get_attribute("placeholder"),
                    ))
                    if fields:
                        forms.append(LoginFormInfo(
                            action_url=base_url,
                            method="POST",
                            fields=fields,
                            submit_button_text="Sign In",
                        ))
            except Exception as e:
                logger.debug(f"Playwright form detection failed: {e}")

        return forms

    def _classify_auth_endpoints(self):
        """Classify all network requests as auth endpoints if they match auth patterns"""
        auth_patterns = [
            r"/login", r"/signin", r"/auth", r"/oauth", r"/token",
            r"/session", r"/api/auth", r"/api/login", r"/authenticate",
            r"/sso", r"/saml", r"/adfs", r"/common/oauth2",
            r"/ppsecure", r"/credential", r"/v2\.0/authorize",
            r"/challenge", r"/verify", r"/2fa", r"/mfa",
            r"/api/signin", r"/api/session", r"/api/authenticate",
            r"/authn", r"/oauth/token", r"/oauth/authorize",
            r"/authorize", r"/idp", r"/idp/auth",
        ]
        for req in self.network_requests:
            url_lower = req["url"].lower()
            for pattern in auth_patterns:
                if re.search(pattern, url_lower):
                    if req["url"] not in self.auth_endpoints:
                        self.auth_endpoints.append(req["url"])
                    break

    def _build_domain_map(self, target_url: str) -> list[DiscoveredDomain]:
        """Build complete domain map with auth and CDN classification"""
        target_parsed = urlparse(target_url)
        base_domain = self._extract_base_domain(target_parsed.netloc)

        domain_map: dict[str, DiscoveredDomain] = {}

        cdn_indicators = ["cdn", "static", "assets", "img", "fonts", "media", "cloudflare", "akamai", "s3"]
        auth_indicators = [
            "login", "auth", "sso", "oauth", "account", "id",
            "adfs", "sts", "microsoftonline", "okta", "azure",
            "accounts", "signin", "authenticate", "idp",
        ]

        for full_domain in self.domains_seen:
            bd = self._extract_base_domain(full_domain)
            subdomain = full_domain.replace(f".{bd}", "").replace(bd, "")
            if subdomain.endswith("."):
                subdomain = subdomain[:-1]

            if bd not in domain_map:
                domain_map[bd] = DiscoveredDomain(
                    domain=bd,
                    subdomains=[],
                    is_auth_related=False,
                    is_cdn=False,
                )

            if subdomain and subdomain not in domain_map[bd].subdomains:
                domain_map[bd].subdomains.append(subdomain)

            domain_lower = full_domain.lower()
            if any(ind in domain_lower for ind in auth_indicators):
                domain_map[bd].is_auth_related = True
            if any(ind in domain_lower for ind in cdn_indicators):
                domain_map[bd].is_cdn = True

        # Ensure target domain is marked as auth-related
        if base_domain in domain_map:
            domain_map[base_domain].is_auth_related = True

        return list(domain_map.values())

    def _detect_post_login_url(self) -> Optional[str]:
        """Detect URL user is redirected to after successful login"""
        common_post_login = [
            "/dashboard", "/home", "/main", "/portal", "/account",
            "/app", "/inbox", "/feed", "/my", "/workspace",
            "/console", "/admin", "/profile", "/overview",
            "/callback", "/signin-oidc", "/auth/complete",
            "/oauth/callback", "/api/callback", "/return",
        ]
        
        # Check redirect chain in reverse
        for url in reversed(self.redirect_chain):
            parsed = urlparse(url)
            for pattern in common_post_login:
                if parsed.path.lower().startswith(pattern):
                    return parsed.path

        # Fallback to network requests
        for req in self.network_requests:
            if req.get("resource_type") == "document":
                parsed = urlparse(req["url"])
                for pattern in common_post_login:
                    if parsed.path.lower().startswith(pattern):
                        return parsed.path
        return None

    def _detect_mfa_indicators(self, html: str) -> bool:
        """Detect if page has MFA/2FA indicators"""
        mfa_patterns = [
            r"two.?factor", r"2fa", r"mfa", r"multi.?factor",
            r"verification.?code", r"authenticator", r"otp",
            r"one.?time.?password", r"security.?code",
            r"enter.?code", r"sms", r"totp", r"security.?key",
        ]
        html_lower = html.lower()
        return any(re.search(p, html_lower) for p in mfa_patterns)

    def _detect_js_auth(self, html: str) -> bool:
        """Detect if authentication uses JavaScript/SPA"""
        js_auth_patterns = [
            r"fetch\s*\(.*/login", r"fetch\s*\(.*/auth",
            r"XMLHttpRequest.*login", r"axios.*login",
            r"\.post\s*\(.*/api/auth", r"firebase\.auth",
            r"React\.", r"Vue\.", r"Angular\.",
            r"\"api/v\d+/auth", r"\"api/v\d+/login",
        ]
        return any(re.search(p, html, re.IGNORECASE) for p in js_auth_patterns)

    def _detect_auth_type(self, html: str, forms: list[LoginFormInfo]) -> Optional[str]:
        """Detect the type of authentication used"""
        html_lower = html.lower()
        
        if "oauth" in html_lower or "openid" in html_lower:
            return "oauth"
        elif "saml" in html_lower:
            return "saml"
        elif "oidc" in html_lower:
            return "oidc"
        elif "kerberos" in html_lower:
            return "kerberos"
        elif "ldap" in html_lower:
            return "ldap"
        elif any("microsoft" in d.lower() or "live" in d.lower() for d in self.domains_seen):
            return "microsoft"
        elif any("okta" in d.lower() for d in self.domains_seen):
            return "okta"
        elif any("google" in d.lower() or "accounts" in d.lower() for d in self.domains_seen):
            return "google"
        elif forms:
            # Check form fields for clues
            for form in forms:
                field_names = {f.field_name.lower() for f in form.fields}
                if any(x in field_names for x in ["username", "email", "login", "userid"]):
                    return "form_based"
        
        return "unknown"

    def _extract_domains_from_js(self, html: str):
        """Extract domain references from scripts and inline JS"""
        soup = BeautifulSoup(html, "html.parser")

        # From script src attributes
        for script in soup.find_all("script", src=True):
            src = script["src"]
            if src.startswith("//"):
                src = "https:" + src
            parsed = urlparse(src)
            if parsed.netloc:
                self.domains_seen.add(parsed.netloc)

        # From inline script content
        url_pattern = re.compile(
            r'(?:https?://|//)([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)'
        )
        for script in soup.find_all("script"):
            if script.string:
                for match in url_pattern.finditer(script.string):
                    domain = match.group(1)
                    if "." in domain and not domain.endswith((".js", ".css", ".png", ".jpg")):
                        self.domains_seen.add(domain)

    def _extract_base_domain(self, domain: str) -> str:
        """Extract base domain from FQDN (e.g., example.com from sub.example.com)"""
        if not domain:
            return domain
        
        parts = domain.split(".")
        if len(parts) <= 2:
            return domain
        
        # Common TLDs to handle correctly
        if len(parts) >= 3 and parts[-2] in ["co", "gov", "ac", "com"]:
            return ".".join(parts[-3:])
        
        return ".".join(parts[-2:])
