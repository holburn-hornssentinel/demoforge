"""AI-powered product analysis using Gemini structured outputs."""

from datetime import datetime
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch
from pydantic import HttpUrl

from demoforge.models import AnalysisResult


class AIAnalyzer:
    """Analyzes product information using Gemini AI with structured outputs."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp") -> None:
        """Initialize the AI analyzer.

        Args:
            api_key: Google API key
            model: Gemini model ID to use
        """
        self.client = genai.Client(api_key=api_key)
        self.model_id = model

    def _generate_with_schema(self, prompt: str) -> AnalysisResult:
        """Generate structured output using Gemini.

        Args:
            prompt: Analysis prompt

        Returns:
            Structured analysis result

        Raises:
            google.api_core.exceptions.GoogleAPIError: If API call fails
        """
        # Generate response with structured output
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )

        # Parse JSON response into Pydantic model
        import json
        data = json.loads(response.text)
        return AnalysisResult.model_validate(data)

    def analyze_repo(
        self, repo_content: str, repo_metadata: dict[str, Any]
    ) -> AnalysisResult:
        """Analyze a GitHub repository using Gemini.

        Args:
            repo_content: Packed repository content from repomix
            repo_metadata: Repository metadata (name, owner, url, etc.)

        Returns:
            Structured analysis result

        Raises:
            google.api_core.exceptions.GoogleAPIError: If API call fails
        """
        current_time = datetime.now().isoformat()
        prompt = f"""Analyze this GitHub repository and extract key product information for creating a demo video.

Repository: {repo_metadata.get('name', 'Unknown')}
Owner: {repo_metadata.get('owner', 'Unknown')}
URL: {repo_metadata.get('url', 'Unknown')}

Repository Content:
{repo_content[:50000]}

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

Return a JSON object with this exact structure:
{{
  "product_name": "string",
  "tagline": "string",
  "category": "string",
  "target_users": ["string"],
  "key_features": [
    {{
      "name": "string",
      "description": "string",
      "importance": 1-10,
      "demo_worthy": boolean
    }}
  ],
  "tech_stack": ["string"],
  "use_cases": ["string"],
  "competitive_advantage": "string",
  "github_url": "{repo_metadata.get('url', '')}",
  "website_url": null,
  "demo_urls": ["string"],
  "analyzed_at": "{current_time}"
}}
"""

        result = self._generate_with_schema(prompt)

        # Override with known metadata
        if repo_metadata.get("url"):
            result.github_url = HttpUrl(repo_metadata["url"])

        return result

    def analyze_website(self, web_content: dict[str, Any]) -> AnalysisResult:
        """Analyze a website using Gemini.

        Args:
            web_content: Website content extracted by WebAnalyzer

        Returns:
            Structured analysis result

        Raises:
            google.api_core.exceptions.GoogleAPIError: If API call fails
        """
        current_time = datetime.now().isoformat()
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

Return a JSON object with this exact structure:
{{
  "product_name": "string",
  "tagline": "string",
  "category": "string",
  "target_users": ["string"],
  "key_features": [
    {{
      "name": "string",
      "description": "string",
      "importance": 1-10,
      "demo_worthy": boolean
    }}
  ],
  "tech_stack": ["string"],
  "use_cases": ["string"],
  "competitive_advantage": "string",
  "github_url": null,
  "website_url": "{url}",
  "demo_urls": ["string"],
  "analyzed_at": "{current_time}"
}}
"""

        result = self._generate_with_schema(prompt)

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
            google.api_core.exceptions.GoogleAPIError: If API call fails
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

Return a JSON object with this exact structure:
{
  "product_name": "string",
  "tagline": "string",
  "category": "string",
  "target_users": ["string"],
  "key_features": [
    {
      "name": "string",
      "description": "string",
      "importance": 1-10,
      "demo_worthy": boolean
    }
  ],
  "tech_stack": ["string"],
  "use_cases": ["string"],
  "competitive_advantage": "string",
  "github_url": null,
  "website_url": null,
  "demo_urls": ["string"],
  "analyzed_at": "ISO datetime string"
}
""")

        prompt = "\n".join(prompt_parts)
        result = self._generate_with_schema(prompt)

        # Override with known metadata
        if repo_metadata and repo_metadata.get("url"):
            result.github_url = HttpUrl(repo_metadata["url"])
        if web_content and web_content.get("url"):
            result.website_url = HttpUrl(web_content["url"])

        return result
