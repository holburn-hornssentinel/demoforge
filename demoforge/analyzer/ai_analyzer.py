"""AI-powered product analysis using Claude structured outputs."""

from typing import Any

from anthropic import Anthropic
from pydantic import HttpUrl

from demoforge.models import AnalysisResult, ProductFeature


class AIAnalyzer:
    """Analyzes product information using Claude AI with structured outputs."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> None:
        """Initialize the AI analyzer.

        Args:
            api_key: Anthropic API key
            model: Claude model ID to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def analyze_repo(
        self, repo_content: str, repo_metadata: dict[str, Any]
    ) -> AnalysisResult:
        """Analyze a GitHub repository using Claude.

        Args:
            repo_content: Packed repository content from repomix
            repo_metadata: Repository metadata (name, owner, url, etc.)

        Returns:
            Structured analysis result

        Raises:
            anthropic.APIError: If API call fails
        """
        prompt = f"""Analyze this GitHub repository and extract key product information for creating a demo video.

Repository: {repo_metadata.get('name', 'Unknown')}
Owner: {repo_metadata.get('owner', 'Unknown')}
URL: {repo_metadata.get('url', 'Unknown')}

Repository Content:
{repo_content[:50000]}  # Limit to ~50k chars to avoid context limits

Your task:
1. Identify the product name and tagline
2. Categorize the product (e.g., "Web framework", "Database", "CLI tool")
3. List target users/personas
4. Extract 5-10 key features with importance scores (1-10)
5. Identify the tech stack
6. List 3-5 common use cases
7. Describe the competitive advantage
8. Suggest 3-5 URLs that would be good to capture for the demo (if website/docs exist)

Focus on information that would be valuable for creating a compelling demo video.
Mark features as "demo_worthy: true" if they should be shown visually in the video.
"""

        # Use structured outputs via messages.parse()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,  # Lower temperature for more consistent extraction
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=AnalysisResult,
        )

        # The response is already parsed into AnalysisResult
        result = response

        # Override with known metadata
        if repo_metadata.get("url"):
            result.github_url = HttpUrl(repo_metadata["url"])

        return result

    def analyze_website(self, web_content: dict[str, Any]) -> AnalysisResult:
        """Analyze a website using Claude.

        Args:
            web_content: Website content extracted by WebAnalyzer

        Returns:
            Structured analysis result

        Raises:
            anthropic.APIError: If API call fails
        """
        content_data = web_content.get("content", {})
        url = web_content.get("url", "Unknown")

        # Format headings
        headings_text = "\n".join(
            f"{'#' * h['level']} {h['text']}" for h in content_data.get("headings", [])
        )

        # Format links
        links_text = "\n".join(
            f"- {link['text']}: {link['href']}"
            for link in content_data.get("links", [])[:15]
        )

        prompt = f"""Analyze this website and extract key product information for creating a demo video.

Website URL: {url}
Title: {content_data.get('title', 'Unknown')}
Description: {content_data.get('description', 'N/A')}

Page Structure (Headings):
{headings_text}

Key Links:
{links_text}

Main Content:
{content_data.get('text_content', '')[:3000]}

Your task:
1. Identify the product name and tagline
2. Categorize the product
3. List target users/personas
4. Extract 5-10 key features with importance scores (1-10)
5. Identify the tech stack (if mentioned)
6. List 3-5 common use cases
7. Describe the competitive advantage
8. Suggest 3-5 specific page URLs that would be good to capture for the demo

Focus on information that would be valuable for creating a compelling demo video.
Mark features as "demo_worthy: true" if they should be shown visually in the video.
"""

        # Use structured outputs via messages.parse()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=AnalysisResult,
        )

        result = response

        # Override with known metadata
        if url:
            result.website_url = HttpUrl(url)

        return result

    def analyze_combined(
        self,
        repo_content: str | None = None,
        repo_metadata: dict[str, Any] | None = None,
        web_content: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """Analyze product using both repository and website data.

        Args:
            repo_content: Packed repository content from repomix
            repo_metadata: Repository metadata
            web_content: Website content from WebAnalyzer

        Returns:
            Combined structured analysis result

        Raises:
            anthropic.APIError: If API call fails
            ValueError: If neither repo nor web content provided
        """
        if not repo_content and not web_content:
            raise ValueError("Must provide either repo_content or web_content")

        # Build comprehensive prompt
        prompt_parts = [
            "Analyze this product using the provided information and extract key details for creating a demo video.\n"
        ]

        # Add repository information
        if repo_content and repo_metadata:
            prompt_parts.append(f"""
GitHub Repository:
- Name: {repo_metadata.get('name', 'Unknown')}
- Owner: {repo_metadata.get('owner', 'Unknown')}
- URL: {repo_metadata.get('url', 'Unknown')}

Repository Content:
{repo_content[:30000]}
""")

        # Add website information
        if web_content:
            content_data = web_content.get("content", {})
            url = web_content.get("url", "Unknown")
            headings_text = "\n".join(
                f"{'#' * h['level']} {h['text']}"
                for h in content_data.get("headings", [])
            )

            prompt_parts.append(f"""
Website:
- URL: {url}
- Title: {content_data.get('title', 'Unknown')}
- Description: {content_data.get('description', 'N/A')}

Page Headings:
{headings_text}

Main Content:
{content_data.get('text_content', '')[:2000]}
""")

        prompt_parts.append("""
Your task:
1. Identify the product name and tagline
2. Categorize the product
3. List target users/personas
4. Extract 5-10 key features with importance scores (1-10)
5. Identify the tech stack
6. List 3-5 common use cases
7. Describe the competitive advantage
8. Suggest 3-5 URLs that would be good to capture for the demo

Synthesize information from all provided sources to create a comprehensive analysis.
Mark features as "demo_worthy: true" if they should be shown visually in the video.
""")

        prompt = "\n".join(prompt_parts)

        # Use structured outputs via messages.parse()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=AnalysisResult,
        )

        result = response

        # Override with known metadata
        if repo_metadata and repo_metadata.get("url"):
            result.github_url = HttpUrl(repo_metadata["url"])
        if web_content and web_content.get("url"):
            result.website_url = HttpUrl(web_content["url"])

        return result
