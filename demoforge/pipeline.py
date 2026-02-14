"""Pipeline orchestrator for DemoForge.

Coordinates the full pipeline: analyze → script → capture → voice → assemble
"""

import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import HttpUrl

from demoforge.analyzer import AIAnalyzer, RepoAnalyzer, WebAnalyzer
from demoforge.assembler import SubtitleGenerator, VideoCompositor
from demoforge.assembler.overlays import OverlayGenerator
from demoforge.cache import PipelineCache
from demoforge.capturer import BrowserCapturer
from demoforge.capturer.annotator import ScreenshotAnnotator
from demoforge.capturer.auth import AuthenticatedCapturer, AuthManager
from demoforge.capturer.fallback import TitleCardGenerator
from demoforge.capturer.vision_analyzer import VisionAnalyzer
from demoforge.models import (
    AnalysisResult,
    AppConfig,
    AudienceType,
    DemoScript,
    Language,
    PipelineProgress,
    PipelineStage,
    ProjectState,
    SceneType,
    Screenshot,
)
from demoforge.scripter import ScriptGenerator
from demoforge.voice import create_tts_engine

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

        # Initialize cache
        self.cache = PipelineCache(
            cache_dir=config.cache_dir,
            enabled=config.enable_caching,
            ttl_hours=config.cache_ttl_hours,
        )

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

        # Initialize capture components
        self.browser_capturer = BrowserCapturer(
            headless=config.browser.headless,
            timeout=config.browser.timeout,
            viewport_width=config.browser.viewport_width,
            viewport_height=config.browser.viewport_height,
            output_dir=config.output_dir / "screenshots",
        )

        # Wrap with authenticated capturer if auth is configured
        self.auth_manager: AuthManager | None = None
        self.authenticated_capturer: AuthenticatedCapturer | None = None
        if config.browser.auth:
            self.auth_manager = AuthManager(state_dir=config.cache_dir / "auth")
            self.authenticated_capturer = AuthenticatedCapturer(
                browser_capturer=self.browser_capturer,
                auth_manager=self.auth_manager,
            )

        self.title_card_generator = TitleCardGenerator(
            output_dir=config.output_dir / "screenshots"
        )

        # Initialize vision analysis components (optional)
        self.vision_analyzer: VisionAnalyzer | None = None
        self.screenshot_annotator: ScreenshotAnnotator | None = None
        if config.vision_enabled:
            self.vision_analyzer = VisionAnalyzer(
                credentials_path=config.google_application_credentials
            )
            self.screenshot_annotator = ScreenshotAnnotator()

        # Initialize voice components
        self.tts_engine = create_tts_engine(
            engine=config.tts.engine,
            voice=config.tts.voice,
            speed=config.tts.speed,
            output_dir=config.output_dir / "audio",
            voice_sample_path=config.tts.voice_sample_path,
        )

        # Initialize subtitle generator
        self.subtitle_generator = SubtitleGenerator(
            output_dir=config.output_dir / "subtitles"
        )

        # Initialize overlay generator
        width, height = map(int, config.video.resolution.split("x"))
        self.overlay_generator = OverlayGenerator(
            width=width,
            height=height,
            output_dir=config.output_dir / "overlays",
        )

        # Initialize video compositor
        self.video_compositor = VideoCompositor(
            output_dir=config.output_dir / "videos",
            fps=config.video.fps,
            resolution=config.video.resolution,
            enable_ken_burns=config.video.enable_ken_burns,
            transition_duration=config.video.transition_duration,
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
            "Running AI analysis with Gemini...",
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
        language: Language = Language.ENGLISH,
        progress_callback: ProgressCallback | None = None,
    ) -> DemoScript:
        """Generate demo video script from analysis.

        Args:
            analysis: Product analysis result
            audience: Target audience type
            target_duration: Target video duration in seconds
            language: Narration language
            progress_callback: Optional progress callback

        Returns:
            Generated demo script
        """
        self._emit_progress(
            PipelineStage.SCRIPT, 0.0, "Generating script...", progress_callback
        )

        script = self.script_generator.generate(
            analysis=analysis,
            audience=audience,
            target_duration=target_duration,
            language=language,
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

            # Stage 3: Capture Screenshots
            self._emit_progress(
                PipelineStage.CAPTURE,
                0.0,
                "Capturing screenshots...",
                progress_callback,
            )
            project.screenshots = await self.capture_visuals(
                script=project.script,
                progress_callback=progress_callback,
            )
            project.current_stage = PipelineStage.VOICE

            # Stage 4: Generate Voice
            self._emit_progress(
                PipelineStage.VOICE, 0.0, "Generating voiceover...", progress_callback
            )
            project.audio_segments = await self.generate_voice(
                script=project.script,
                progress_callback=progress_callback,
            )

            # Generate subtitles from audio segments
            project.subtitles, srt_path = self.subtitle_generator.generate_from_audio(
                audio_segments=project.audio_segments,
                project_id=project_id,
            )

            project.current_stage = PipelineStage.ASSEMBLE

            # Stage 5: Assemble Video
            self._emit_progress(
                PipelineStage.ASSEMBLE,
                0.0,
                "Assembling video...",
                progress_callback,
            )

            # Set output path if not provided
            if output_path is None:
                output_path = (
                    self.config.output_dir
                    / "videos"
                    / f"{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                )

            # Assemble video with progress tracking
            def assembly_progress(message: str, progress: float) -> None:
                """Internal progress callback for assembly."""
                self._emit_progress(
                    PipelineStage.ASSEMBLE,
                    progress,
                    message,
                    progress_callback,
                )

            project.output_path = self.video_compositor.assemble_video(
                screenshots=project.screenshots,
                audio_segments=project.audio_segments,
                output_path=output_path,
                subtitle_path=srt_path,
                progress_callback=assembly_progress,
            )

            self._emit_progress(
                PipelineStage.ASSEMBLE,
                1.0,
                f"Video assembled: {project.output_path.name}",
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

    async def _capture_single_scene(
        self,
        scene,
        scene_index: int,
        total_scenes: int,
        semaphore: asyncio.Semaphore,
        progress_lock: asyncio.Lock,
        progress_callback: ProgressCallback | None,
        current_item_ref: list[int],  # Mutable reference for tracking progress
        total_items: int,
    ) -> Screenshot | None:
        """Capture a single scene's visual content.

        Args:
            scene: Scene to capture
            scene_index: Index of this scene (0-based)
            total_scenes: Total number of scenes
            semaphore: Semaphore for concurrency control
            progress_lock: Lock for thread-safe progress updates
            progress_callback: Progress callback
            current_item_ref: Mutable list containing current progress counter
            total_items: Total items for progress calculation

        Returns:
            Screenshot or None if scene type doesn't produce a screenshot
        """
        async with semaphore:
            # Thread-safe progress update
            async with progress_lock:
                current_item_ref[0] += 1
                current_item = current_item_ref[0]
                self._emit_progress(
                    PipelineStage.CAPTURE,
                    current_item / total_items,
                    f"Capturing scene {scene_index+1}/{total_scenes}: {scene.id}",
                    progress_callback,
                    current_scene=current_item,
                    total_scenes=total_items,
                )

            screenshot = None

            if scene.scene_type == SceneType.SCREENSHOT and scene.url:
                # Capture actual webpage screenshot (with auth if configured)
                if self.authenticated_capturer:
                    screenshot = await self.authenticated_capturer.capture_with_auth(
                        url=scene.url,
                        scene_id=scene.id,
                        credentials=self.config.browser.auth,
                    )
                else:
                    screenshot = await self.browser_capturer.capture_screenshot(
                        url=scene.url,
                        scene_id=scene.id,
                        full_page=False,  # Viewport only for consistent sizing
                    )

                # Analyze screenshot with Vision API if enabled
                if screenshot and self.vision_analyzer and self.screenshot_annotator:
                    try:
                        highlights = self.vision_analyzer.suggest_highlights(
                            screenshot.path
                        )
                        if highlights:
                            # Store highlights in metadata
                            if screenshot.metadata is None:
                                screenshot.metadata = {}
                            screenshot.metadata["highlights"] = highlights
                    except Exception as e:
                        # Don't fail the pipeline if vision analysis fails
                        print(f"Warning: Vision analysis failed for {scene.id}: {e}")

            elif scene.scene_type == SceneType.TITLE_CARD:
                # Generate title card
                text = scene.visual_content or scene.narration
                screenshot = self.title_card_generator.generate_title_card(
                    text=text,
                    scene_id=scene.id,
                )

            elif scene.scene_type == SceneType.CODE_SNIPPET:
                # Generate code snippet image
                code = scene.visual_content
                screenshot = self.title_card_generator.generate_code_snippet(
                    code=code,
                    scene_id=scene.id,
                )

            elif scene.scene_type == SceneType.DIAGRAM:
                # Generate diagram placeholder (Phase 3 will add Mermaid rendering)
                diagram_label = "📊 DIAGRAM"
                diagram_content = scene.visual_content or scene.narration
                text = f"{diagram_label}\n\n{diagram_content}"
                screenshot = self.title_card_generator.generate_title_card(
                    text=text,
                    scene_id=scene.id,
                )

            return screenshot

    async def capture_visuals(
        self,
        script: DemoScript,
        progress_callback: ProgressCallback | None = None,
    ) -> list[Screenshot]:
        """Capture screenshots and generate visual content for all narrated segments.

        Creates visuals for intro, all scenes, and outro.
        Scenes are captured in parallel (controlled by parallel_screenshots config).

        Args:
            script: Demo script with scene definitions
            progress_callback: Optional progress callback

        Returns:
            List of captured screenshots (intro + scenes + outro)
        """
        screenshots = []
        # Total includes intro + scenes + outro
        total_items = 1 + len(script.scenes) + 1
        current_item_ref = [0]  # Mutable reference for thread-safe counter

        # Generate intro card if intro text exists
        if script.intro:
            current_item_ref[0] += 1
            self._emit_progress(
                PipelineStage.CAPTURE,
                current_item_ref[0] / total_items,
                "Capturing intro card",
                progress_callback,
                current_scene=current_item_ref[0],
                total_scenes=total_items,
            )

            intro_screenshot = self.title_card_generator.generate_title_card(
                text=script.intro,
                scene_id="intro",
            )
            screenshots.append(intro_screenshot)

        # Capture scene visuals in parallel
        if script.scenes:
            # Create semaphore for concurrency control and progress lock
            semaphore = asyncio.Semaphore(self.config.parallel_screenshots)
            progress_lock = asyncio.Lock()

            # Create tasks for all scenes
            tasks = [
                self._capture_single_scene(
                    scene=scene,
                    scene_index=i,
                    total_scenes=len(script.scenes),
                    semaphore=semaphore,
                    progress_lock=progress_lock,
                    progress_callback=progress_callback,
                    current_item_ref=current_item_ref,
                    total_items=total_items,
                )
                for i, scene in enumerate(script.scenes)
            ]

            # Execute in parallel while maintaining order
            scene_screenshots = await asyncio.gather(*tasks)

            # Add non-None screenshots (maintaining order)
            for screenshot in scene_screenshots:
                if screenshot:
                    screenshots.append(screenshot)

        # Generate outro card if outro text exists
        if script.outro:
            current_item_ref[0] += 1
            self._emit_progress(
                PipelineStage.CAPTURE,
                current_item_ref[0] / total_items,
                "Capturing outro card",
                progress_callback,
                current_scene=current_item_ref[0],
                total_scenes=total_items,
            )

            outro_screenshot = self.title_card_generator.generate_title_card(
                text=script.outro,
                scene_id="outro",
            )
            screenshots.append(outro_screenshot)

        self._emit_progress(
            PipelineStage.CAPTURE,
            1.0,
            f"Captured {len(screenshots)} visuals",
            progress_callback,
        )

        return screenshots

    async def generate_voice(
        self,
        script: DemoScript,
        progress_callback: ProgressCallback | None = None,
    ) -> list:
        """Generate voiceover audio for all narration.

        Args:
            script: Demo script with narration
            progress_callback: Optional progress callback

        Returns:
            List of AudioSegment objects
        """
        from demoforge.models import AudioSegment

        audio_segments = []
        current_time = 0.0

        # Collect all narration segments (intro, scenes, outro)
        narrations = []

        if script.intro:
            narrations.append(("intro", script.intro))

        for scene in script.scenes:
            if scene.narration:
                narrations.append((scene.id, scene.narration))

        if script.outro:
            narrations.append(("outro", script.outro))

        total_segments = len(narrations)

        # Generate audio for each segment
        for i, (segment_id, text) in enumerate(narrations):
            segment_num = i + 1
            progress = segment_num / total_segments

            self._emit_progress(
                PipelineStage.VOICE,
                progress,
                f"Synthesizing audio {segment_num}/{total_segments}: {segment_id}",
                progress_callback,
                current_scene=segment_num,
                total_scenes=total_segments,
            )

            # Synthesize audio
            audio = await self.tts_engine.synthesize(
                text=text,
                scene_id=segment_id,
            )

            # Set start time in video
            audio.start_time = current_time
            current_time += audio.duration_seconds

            audio_segments.append(audio)

        self._emit_progress(
            PipelineStage.VOICE,
            1.0,
            f"Generated {len(audio_segments)} audio segments "
            f"({current_time:.1f}s total)",
            progress_callback,
        )

        return audio_segments

    async def cleanup(self) -> None:
        """Clean up resources (close browser, etc.)."""
        await self.web_analyzer.close()
        await self.browser_capturer.close()


def create_pipeline(config: AppConfig) -> Pipeline:
    """Factory function to create a Pipeline instance.

    Args:
        config: Application configuration

    Returns:
        Configured Pipeline instance
    """
    return Pipeline(config)
