"""Authentication support for capturing protected pages."""

import json
from pathlib import Path

from playwright.async_api import BrowserContext, Page
from pydantic import HttpUrl

from demoforge.models import AuthCredentials


class AuthManager:
    """Manages authentication for browser sessions."""

    def __init__(self, state_dir: Path = Path("/app/cache/auth")) -> None:
        """Initialize auth manager.

        Args:
            state_dir: Directory to store authentication state
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, domain: str) -> Path:
        """Get path to auth state file for a domain.

        Args:
            domain: Domain name (e.g., "example.com")

        Returns:
            Path to state file
        """
        # Sanitize domain name for filename
        safe_domain = domain.replace(":", "_").replace("/", "_")
        return self.state_dir / f"{safe_domain}_auth.json"

    async def save_auth_state(
        self, context: BrowserContext, domain: str
    ) -> None:
        """Save authentication state (cookies, localStorage) for reuse.

        Args:
            context: Playwright browser context
            domain: Domain name
        """
        state_path = self.get_state_path(domain)
        state = await context.storage_state()

        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)

    async def load_auth_state(
        self, context: BrowserContext, domain: str
    ) -> bool:
        """Load saved authentication state into context.

        Args:
            context: Playwright browser context
            domain: Domain name

        Returns:
            True if state was loaded, False if no saved state exists
        """
        state_path = self.get_state_path(domain)

        if not state_path.exists():
            return False

        with open(state_path) as f:
            state = json.load(f)

        # Apply saved state to context
        await context.add_cookies(state.get("cookies", []))

        return True

    async def login_with_credentials(
        self,
        page: Page,
        credentials: AuthCredentials,
    ) -> None:
        """Perform login using credentials.

        Args:
            page: Playwright page
            credentials: Login credentials and selectors

        Raises:
            playwright.async_api.Error: If login fails
        """
        # Navigate to login page
        await page.goto(str(credentials.login_url), wait_until="networkidle")

        # Fill username
        await page.fill(credentials.username_selector, credentials.username)

        # Fill password
        await page.fill(credentials.password_selector, credentials.password)

        # Click submit and wait for navigation
        async with page.expect_navigation(wait_until="networkidle"):
            await page.click(credentials.submit_selector)

    def clear_auth_state(self, domain: str) -> None:
        """Clear saved authentication state for a domain.

        Args:
            domain: Domain name
        """
        state_path = self.get_state_path(domain)
        if state_path.exists():
            state_path.unlink()


class AuthenticatedCapturer:
    """Browser capturer with authentication support."""

    def __init__(
        self,
        browser_capturer,
        auth_manager: AuthManager | None = None,
    ) -> None:
        """Initialize authenticated capturer.

        Args:
            browser_capturer: BrowserCapturer instance
            auth_manager: Optional auth manager (creates new if not provided)
        """
        self.capturer = browser_capturer
        self.auth_manager = auth_manager or AuthManager()

    async def capture_with_auth(
        self,
        url: HttpUrl,
        scene_id: str,
        credentials: AuthCredentials | None = None,
        domain: str | None = None,
    ):
        """Capture screenshot with authentication.

        Args:
            url: URL to capture
            scene_id: Scene identifier
            credentials: Optional credentials for login
            domain: Domain for auth state persistence

        Returns:
            Screenshot metadata
        """
        # Extract domain from URL if not provided
        if domain is None:
            domain = str(url).split("//")[1].split("/")[0]

        browser = await self.capturer._get_browser()

        # Create context with persistent state
        context = await browser.new_context(
            viewport={
                "width": self.capturer.viewport_width,
                "height": self.capturer.viewport_height,
            }
        )

        try:
            # Try to load saved auth state
            state_loaded = await self.auth_manager.load_auth_state(
                context, domain
            )

            # If no saved state and credentials provided, perform login
            if not state_loaded and credentials:
                page = await context.new_page()
                await self.auth_manager.login_with_credentials(page, credentials)
                await self.auth_manager.save_auth_state(context, domain)
                await page.close()

            # Now capture the protected page
            page = await context.new_page()
            await page.goto(str(url), wait_until="networkidle")

            # Generate filename
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{scene_id}_{timestamp}.png"
            image_path = self.capturer.output_dir / filename

            # Capture screenshot
            await page.screenshot(path=str(image_path), type="png")

            # Get dimensions
            dimensions = await page.evaluate(
                """() => {
                return {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                }
            }"""
            )

            from demoforge.models import Screenshot

            return Screenshot(
                scene_id=scene_id,
                url=url,
                image_path=image_path,
                width=dimensions["width"],
                height=dimensions["height"],
                captured_at=datetime.now(),
            )

        finally:
            await context.close()
