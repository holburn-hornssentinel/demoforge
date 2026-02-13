"""Pipeline orchestrator for DemoForge.

Coordinates the full pipeline: analyze → script → capture → voice → assemble
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import HttpUrl

from demoforge.analyzer import AIAnalyzer, RepoAnalyzer, WebAnalyzer
from demoforge.models import (
    AnalysisResult,
    AppConfig,
    AudienceType,
    DemoScript,
    PipelineProgress,
    PipelineStage,
    ProjectState,
)
from demoforge.scripter import ScriptGenerator

# Type alias for progress callback
ProgressCallback = Callable[[PipelineProgress], None]


class Pipeline:
    """Orchestrates the full demo video generation pipeline."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the pipeline.

        Args:
            config: Application configuration
        """
        self.config = config

        # Initialize analyzers
        self.repo_analyzer = RepoAnalyzer(cache_dir=config.cache_dir / "repos")
        self.web_analyzer = WebAnalyzer(
            headless=config.browser.headless,
            timeout=config.browser.timeout,
            viewport_width=config.browser.viewport_width,
            viewport_height=config.browser.viewport_height,
        )
        self.ai_analyzer = AIAnalyzer(
            api_key=config.google_api_key, model=config.gemini_model
        )

        # Initialize script generator
        self.script_generator = ScriptGenerator(
            api_key=config.google_api_key, model=config.gemini_model
        )

        # Pipeline state
        self.current_progress: PipelineProgress | None = None

    def _emit_progress(
        self,
        stage: PipelineStage,
        progress: float,
        message: str,
        callback: ProgressCallback | None = None,
        current_scene: int = 0,
        total_scenes: int = 0,
    ) -> None:
        """Emit progress update.

        Args:
            stage: Current pipeline stage
            progress: Progress percentage (0.0 to 1.0)
            message: Human-readable status message
            callback: Optional progress callback function
            current_scene: Current scene being processed
            total_scenes: Total number of scenes
        """
        self.current_progress = PipelineProgress(
            stage=stage,
            progress=progress,
            message=message,
            current_scene=current_scene,
            total_scenes=total_scenes,
            updated_at=datetime.now(),
        )

        if callback:
            callback(self.current_progress)

    def _compute_cache_hash(
        self,
        repo_url: HttpUrl | None,
        website_url: HttpUrl | None,
        audience: AudienceType,
        target_length: int,
    ) -> str:
        """Compute cache hash for pipeline inputs.

        Args:
            repo_url: GitHub repository URL
            website_url: Website URL
            audience: Target audience
            target_length: Target video length

        Returns:
            SHA256 hash of inputs
        """
        inputs = {
            "repo_url": str(repo_url) if repo_url else None,
            "website_url": str(website_url) if website_url else None,
            "audience": audience.value,
            "target_length": target_length,
        }
        inputs_str = json.dumps(inputs, sort_keys=True)
        return hashlib.sha256(inputs_str.encode()).hexdigest()

    async def analyze(
        self,
        repo_url: HttpUrl | None = None,
        website_url: HttpUrl | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisResult:
        """Analyze a product from repository and/or website.

        Args:
            repo_url: GitHub repository URL
            website_url: Website URL
            progress_callback: Optional progress callback

        Returns:
            Product analysis result

        Raises:
            ValueError: If neither repo_url nor website_url provided
        """
        if not repo_url and not website_url:
            raise ValueError("Must provide either repo_url or website_url")

        self._emit_progress(
            PipelineStage.ANALYZE, 0.0, "Starting analysis...", progress_callback
        )

        repo_content = None
        repo_metadata = None
        web_content = None

        # Analyze repository if provided
        if repo_url:
            self._emit_progress(
                PipelineStage.ANALYZE,
                0.2,
                f"Cloning repository: {repo_url}",
                progress_callback,
            )
            repo_data = self.repo_analyzer.analyze(repo_url)
            repo_content = repo_data["packed_content"]
            repo_metadata = repo_data["metadata"]

        # Analyze website if provided
        if website_url:
            self._emit_progress(
                PipelineStage.ANALYZE,
                0.5,
                f"Scraping website: {website_url}",
                progress_callback,
            )
            web_content = await self.web_analyzer.analyze(website_url)

        # Run AI analysis
        self._emit_progress(
            PipelineStage.ANALYZE,
            0.7,
            "Running AI analysis with Claude...",
            progress_callback,
        )

        if repo_content and web_content:
            analysis = self.ai_analyzer.analyze_combined(
                repo_content=repo_content,
                repo_metadata=repo_metadata,
                web_content=web_content,
            )
        elif repo_content:
            analysis = self.ai_analyzer.analyze_repo(repo_content, repo_metadata or {})
        else:
            analysis = self.ai_analyzer.analyze_website(web_content or {})

        self._emit_progress(
            PipelineStage.ANALYZE, 1.0, "Analysis complete", progress_callback
        )

        return analysis

    def generate_script(
        self,
        analysis: AnalysisResult,
        audience: AudienceType = AudienceType.DEVELOPER,
        target_duration: int = 90,
        progress_callback: ProgressCallback | None = None,
    ) -> DemoScript:
        """Generate demo video script from analysis.

        Args:
            analysis: Product analysis result
            audience: Target audience type
            target_duration: Target video duration in seconds
            progress_callback: Optional progress callback

        Returns:
            Generated demo script
        """
        self._emit_progress(
            PipelineStage.SCRIPT, 0.0, "Generating script...", progress_callback
        )

        script = self.script_generator.generate(
            analysis=analysis, audience=audience, target_duration=target_duration
        )

        self._emit_progress(
            PipelineStage.SCRIPT,
            1.0,
            f"Script generated: {len(script.scenes)} scenes, {script.total_words} words",
            progress_callback,
        )

        return script

    async def generate_full_pipeline(
        self,
        project_id: str,
        repo_url: HttpUrl | None = None,
        website_url: HttpUrl | None = None,
        audience: AudienceType = AudienceType.DEVELOPER,
        target_duration: int = 90,
        output_path: Path | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> ProjectState:
        """Execute the full pipeline: analyze → script → capture → voice → assemble.

        Args:
            project_id: Unique project identifier
            repo_url: GitHub repository URL
            website_url: Website URL
            audience: Target audience type
            target_duration: Target video duration in seconds
            output_path: Output video file path
            progress_callback: Optional progress callback

        Returns:
            Final project state

        Raises:
            ValueError: If neither repo_url nor website_url provided
        """
        # Create project state
        project = ProjectState(
            id=project_id,
            name=project_id,
            repo_url=repo_url,
            website_url=website_url,
            audience=audience,
            target_length=target_duration,
            output_path=output_path,
        )

        # Compute cache hash
        project.cache_hash = self._compute_cache_hash(
            repo_url, website_url, audience, target_duration
        )

        try:
            # Stage 1: Analyze
            self._emit_progress(
                PipelineStage.ANALYZE, 0.0, "Starting analysis...", progress_callback
            )
            project.analysis = await self.analyze(
                repo_url=repo_url,
                website_url=website_url,
                progress_callback=progress_callback,
            )
            project.current_stage = PipelineStage.SCRIPT

            # Stage 2: Generate Script
            self._emit_progress(
                PipelineStage.SCRIPT, 0.0, "Generating script...", progress_callback
            )
            project.script = self.generate_script(
                analysis=project.analysis,
                audience=audience,
                target_duration=target_duration,
                progress_callback=progress_callback,
            )
            project.current_stage = PipelineStage.CAPTURE

            # Stage 3: Capture Screenshots (placeholder for now)
            self._emit_progress(
                PipelineStage.CAPTURE,
                0.0,
                "Capturing screenshots...",
                progress_callback,
            )
            # TODO: Implement screenshot capture in Phase 2
            self._emit_progress(
                PipelineStage.CAPTURE,
                1.0,
                "Screenshots captured (placeholder)",
                progress_callback,
            )
            project.current_stage = PipelineStage.VOICE

            # Stage 4: Generate Voice (placeholder for now)
            self._emit_progress(
                PipelineStage.VOICE, 0.0, "Generating voiceover...", progress_callback
            )
            # TODO: Implement TTS in Phase 2
            self._emit_progress(
                PipelineStage.VOICE,
                1.0,
                "Voiceover generated (placeholder)",
                progress_callback,
            )
            project.current_stage = PipelineStage.ASSEMBLE

            # Stage 5: Assemble Video (placeholder for now)
            self._emit_progress(
                PipelineStage.ASSEMBLE,
                0.0,
                "Assembling video...",
                progress_callback,
            )
            # TODO: Implement video assembly in Phase 3
            self._emit_progress(
                PipelineStage.ASSEMBLE,
                1.0,
                "Video assembled (placeholder)",
                progress_callback,
            )
            project.current_stage = PipelineStage.COMPLETE

            # Update final state
            project.updated_at = datetime.now()
            self._emit_progress(
                PipelineStage.COMPLETE, 1.0, "Pipeline complete!", progress_callback
            )

        except Exception as e:
            # Handle errors
            project.current_stage = PipelineStage.FAILED
            project.progress = PipelineProgress(
                stage=PipelineStage.FAILED,
                progress=0.0,
                message=f"Pipeline failed: {str(e)}",
                error=str(e),
            )
            raise

        return project

    async def cleanup(self) -> None:
        """Clean up resources (close browser, etc.)."""
        await self.web_analyzer.close()


def create_pipeline(config: AppConfig) -> Pipeline:
    """Factory function to create a Pipeline instance.

    Args:
        config: Application configuration

    Returns:
        Configured Pipeline instance
    """
    return Pipeline(config)
