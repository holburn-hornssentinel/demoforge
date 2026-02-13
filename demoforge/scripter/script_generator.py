"""Script generation using Gemini AI and Jinja2 templates."""

import json
from pathlib import Path

import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader

from demoforge.models import AnalysisResult, AudienceType, DemoScript
from demoforge.scripter.duration import DurationEnforcer


class ScriptGenerator:
    """Generates demo video scripts using Gemini AI."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        templates_dir: Path | None = None,
    ) -> None:
        """Initialize the script generator.

        Args:
            api_key: Google API key
            model: Gemini model ID to use
            templates_dir: Path to Jinja2 templates directory
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )

        # Set up Jinja2 environment
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def _build_system_prompt(
        self,
        analysis: AnalysisResult,
        audience: AudienceType,
        target_duration: int,
    ) -> str:
        """Build system prompt from Jinja2 template.

        Args:
            analysis: Product analysis result
            audience: Target audience type
            target_duration: Target video duration in seconds

        Returns:
            Rendered system prompt
        """
        # Calculate target word count
        enforcer = DurationEnforcer(target_duration)

        # Select template based on audience
        template_name = f"{audience.value}.j2"
        template = self.jinja_env.get_template(template_name)

        # Render template
        return template.render(
            product_name=analysis.product_name,
            tagline=analysis.tagline,
            category=analysis.category,
            target_users=analysis.target_users,
            key_features=[f for f in analysis.key_features if f.demo_worthy],
            tech_stack=analysis.tech_stack,
            use_cases=analysis.use_cases,
            competitive_advantage=analysis.competitive_advantage,
            target_duration=target_duration,
            target_words=enforcer.target_words,
        )

    def generate(
        self,
        analysis: AnalysisResult,
        audience: AudienceType = AudienceType.DEVELOPER,
        target_duration: int = 90,
        max_retries: int = 2,
    ) -> DemoScript:
        """Generate a demo video script.

        Args:
            analysis: Product analysis result
            audience: Target audience type
            target_duration: Target video duration in seconds
            max_retries: Maximum retries if duration is off-target

        Returns:
            Generated demo script

        Raises:
            google.api_core.exceptions.GoogleAPIError: If API call fails
        """
        system_prompt = self._build_system_prompt(analysis, audience, target_duration)
        enforcer = DurationEnforcer(target_duration)

        user_prompt = f"""{system_prompt}

Create a {target_duration}-second demo video script with the following structure:

1. **Title**: Catchy video title
2. **Intro** (opening narration): Hook the audience in the first 5 seconds
3. **Scenes**: 5-10 scenes, each with:
   - Unique scene ID (e.g., "scene_1", "scene_2")
   - Scene type (screenshot, title_card, code_snippet, diagram)
   - Narration text
   - Duration in seconds
   - URL to capture (if screenshot) OR visual_content (if title_card/code)
   - Optional actions (highlight, zoom, pan) - empty array for now
4. **Outro** (closing narration): Wrap up with impact
5. **Call to action**: What should viewers do next?

IMPORTANT:
- Total narration should be approximately {enforcer.target_words} words ({enforcer.min_words}-{enforcer.max_words} acceptable)
- Each scene should be 8-15 seconds
- Use demo_urls from analysis where appropriate: {analysis.demo_urls}
- Narration should be natural and spoken-word friendly (avoid complex sentences)
- Scene durations should sum to approximately {target_duration} seconds
- Set audience to "{audience.value}"
- Set total_duration to {target_duration}
- Set generated_at to current ISO datetime

Return a JSON object with this exact structure:
{{
  "title": "string",
  "audience": "{audience.value}",
  "total_duration": {target_duration},
  "scenes": [
    {{
      "id": "scene_1",
      "scene_type": "screenshot",
      "narration": "string",
      "duration_seconds": 10.0,
      "url": "https://..." or null,
      "visual_content": "",
      "actions": [],
      "metadata": {{}}
    }}
  ],
  "intro": "string",
  "outro": "string",
  "call_to_action": "string",
  "generated_at": "ISO datetime string"
}}
"""

        for attempt in range(max_retries + 1):
            # Generate script
            response = self.model.generate_content(user_prompt)
            data = json.loads(response.text)
            script = DemoScript.model_validate(data)

            # Check if duration is within bounds
            if enforcer.is_within_bounds(script.total_words):
                return script

            # If not, adjust and retry
            if attempt < max_retries:
                adjustment = enforcer.get_adjustment_message(script.total_words)
                user_prompt = f"""{user_prompt}

ADJUSTMENT NEEDED: {adjustment}

Current word count: {script.total_words} (target: {enforcer.target_words})

Please regenerate the script with adjusted narration to hit the target duration.
"""

        # Return best attempt even if not perfect
        return script

    def refine_script(
        self,
        script: DemoScript,
        feedback: str,
    ) -> DemoScript:
        """Refine an existing script based on user feedback.

        Args:
            script: Existing demo script
            feedback: User feedback for refinement

        Returns:
            Refined demo script

        Raises:
            google.api_core.exceptions.GoogleAPIError: If API call fails
        """
        prompt = f"""You previously generated this demo video script:

Title: {script.title}
Audience: {script.audience}
Total Duration: {script.total_duration}s

Current Script:
Intro: {script.intro}

Scenes:
{chr(10).join(f"{i+1}. [{s.scene_type}] {s.narration} ({s.duration_seconds}s)" for i, s in enumerate(script.scenes))}

Outro: {script.outro}
CTA: {script.call_to_action}

User Feedback: {feedback}

Please refine the script based on the feedback while maintaining the target duration ({script.total_duration} seconds).

Return a complete updated DemoScript object in JSON format with the same structure as before.
"""

        response = self.model.generate_content(prompt)
        data = json.loads(response.text)
        return DemoScript.model_validate(data)
