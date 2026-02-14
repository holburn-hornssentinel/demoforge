"""Browser-based screenshot capture using Playwright."""

from datetime import datetime
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright
from pydantic import HttpUrl

from demoforge.models import Screenshot


class BrowserCapturer:
    """Captures screenshots using Playwright at 2x resolution."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        viewport_width: int = 2560,
        viewport_height: int = 1440,
        output_dir: Path = Path("/app/output/screenshots"),
    ) -> None:
        """Initialize browser capturer.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            viewport_width: Browser viewport width (2x resolution for crisp output)
            viewport_height: Browser viewport height
            output_dir: Directory to save screenshots
        """
        self.headless = headless
        self.timeout = timeout
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._browser: Browser | None = None
        self._playwright = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance.

        Returns:
            Playwright browser instance
        """
        if self._browser is None:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
        return self._browser

    async def capture_screenshot(
        self,
        url: HttpUrl,
        scene_id: str,
        wait_for_selector: str | None = None,
        full_page: bool = False,
    ) -> Screenshot:
        """Capture a screenshot of a webpage.

        Args:
            url: URL to capture
            scene_id: Scene identifier
            wait_for_selector: Optional CSS selector to wait for before capturing
            full_page: Capture full scrollable page (default: viewport only)

        Returns:
            Screenshot metadata

        Raises:
            playwright.async_api.Error: If page load or capture fails
        """
        url_str = str(url)
        browser = await self._get_browser()

        # Create new page
        page = await browser.new_page(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )

        try:
            # Navigate to URL
            await page.goto(
                url_str, timeout=self.timeout, wait_until="networkidle"
            )

            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(
                    wait_for_selector, timeout=self.timeout
                )

            # Wait for page to be fully loaded
            await page.wait_for_load_state("domcontentloaded")

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{scene_id}_{timestamp}.png"
            image_path = self.output_dir / filename

            # Capture screenshot
            await page.screenshot(
                path=str(image_path),
                full_page=full_page,
                type="png",
            )

            # Get actual dimensions
            dimensions = await page.evaluate(
                """() => {
                return {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                }
            }"""
            )

            return Screenshot(
                scene_id=scene_id,
                url=url,
                image_path=image_path,
                width=dimensions["width"],
                height=dimensions["height"],
                captured_at=datetime.now(),
            )

        finally:
            await page.close()

    async def capture_multiple(
        self,
        urls: list[tuple[str, HttpUrl]],
        wait_for_selectors: dict[str, str] | None = None,
    ) -> list[Screenshot]:
        """Capture multiple screenshots efficiently.

        Args:
            urls: List of (scene_id, url) tuples
            wait_for_selectors: Optional dict mapping scene_id to CSS selector

        Returns:
            List of screenshot metadata
        """
        screenshots = []
        wait_selectors = wait_for_selectors or {}

        for scene_id, url in urls:
            selector = wait_selectors.get(scene_id)
            screenshot = await self.capture_screenshot(
                url=url,
                scene_id=scene_id,
                wait_for_selector=selector,
            )
            screenshots.append(screenshot)

        return screenshots

    async def close(self) -> None:
        """Close the browser instance."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
