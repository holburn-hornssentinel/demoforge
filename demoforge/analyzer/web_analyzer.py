"""Website analysis using Playwright for scraping."""

from pathlib import Path
from typing import Any

from playwright.async_api import Browser, Page, async_playwright
from pydantic import HttpUrl


class WebAnalyzer:
    """Analyzes websites by scraping content with Playwright."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        viewport_width: int = 2560,
        viewport_height: int = 1440,
    ) -> None:
        """Initialize the web analyzer.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
        """
        self.headless = headless
        self.timeout = timeout
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self._browser: Browser | None = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance.

        Returns:
            Playwright browser instance
        """
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=self.headless)
        return self._browser

    async def _extract_page_content(self, page: Page) -> dict[str, Any]:
        """Extract relevant content from a web page.

        Args:
            page: Playwright page instance

        Returns:
            Dictionary with extracted content:
                - title: Page title
                - description: Meta description
                - text_content: Main text content (cleaned)
                - headings: List of h1-h3 headings
                - links: List of internal links
        """
        # Get page title and meta description
        title = await page.title()
        description = await page.get_attribute('meta[name="description"]', "content") or ""

        # Extract text content (removing scripts and styles)
        text_content = await page.evaluate("""
            () => {
                // Remove script and style elements
                const scripts = document.querySelectorAll('script, style, nav, footer');
                scripts.forEach(el => el.remove());

                // Get visible text
                return document.body.innerText;
            }
        """)

        # Extract headings
        headings = await page.evaluate("""
            () => {
                const headingElements = document.querySelectorAll('h1, h2, h3');
                return Array.from(headingElements).map(h => ({
                    level: parseInt(h.tagName[1]),
                    text: h.innerText.trim()
                }));
            }
        """)

        # Extract internal links
        page_url = page.url
        base_domain = page_url.split("/")[2]
        links = await page.evaluate(f"""
            (baseDomain) => {{
                const linkElements = document.querySelectorAll('a[href]');
                return Array.from(linkElements)
                    .map(a => ({{ href: a.href, text: a.innerText.trim() }}))
                    .filter(link => link.href.includes(baseDomain));
            }}
        """, base_domain)

        return {
            "title": title,
            "description": description,
            "text_content": text_content.strip()[:5000],  # Limit to 5000 chars
            "headings": headings[:20],  # Limit to first 20 headings
            "links": links[:30],  # Limit to first 30 links
        }

    async def analyze(self, url: HttpUrl) -> dict[str, Any]:
        """Analyze a website by scraping its content.

        Args:
            url: Website URL to analyze

        Returns:
            Dictionary with website analysis:
                - url: Analyzed URL
                - content: Extracted content
                - screenshot_path: Path to screenshot (if saved)

        Raises:
            playwright.async_api.Error: If page load fails
        """
        url_str = str(url)
        browser = await self._get_browser()
        page = await browser.new_page(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )

        try:
            # Navigate to the page
            await page.goto(url_str, timeout=self.timeout, wait_until="networkidle")

            # Wait for page to be fully loaded
            await page.wait_for_load_state("domcontentloaded")

            # Extract content
            content = await self._extract_page_content(page)

            return {
                "url": url_str,
                "content": content,
            }

        finally:
            await page.close()

    async def analyze_multiple(self, urls: list[HttpUrl]) -> list[dict[str, Any]]:
        """Analyze multiple websites in parallel.

        Args:
            urls: List of website URLs to analyze

        Returns:
            List of analysis results
        """
        results = []
        for url in urls:
            result = await self.analyze(url)
            results.append(result)
        return results

    async def close(self) -> None:
        """Close the browser instance."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
