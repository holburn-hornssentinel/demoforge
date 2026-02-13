"""GitHub repository analysis using git and repomix."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import HttpUrl


class RepoAnalyzer:
    """Analyzes GitHub repositories by cloning and packing with repomix."""

    def __init__(self, cache_dir: Path = Path("/app/cache/repos")) -> None:
        """Initialize the repository analyzer.

        Args:
            cache_dir: Directory to store cloned repositories
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_hash(self, repo_url: str) -> str:
        """Generate a hash for the repository URL.

        Args:
            repo_url: GitHub repository URL

        Returns:
            SHA256 hash of the URL
        """
        return hashlib.sha256(repo_url.encode()).hexdigest()[:16]

    def _clone_repo(self, repo_url: str, target_dir: Path) -> None:
        """Clone a GitHub repository.

        Args:
            repo_url: GitHub repository URL
            target_dir: Directory to clone into

        Raises:
            subprocess.CalledProcessError: If git clone fails
        """
        # Use shallow clone for speed (depth=1)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

    def _run_repomix(self, repo_dir: Path) -> str:
        """Run repomix to pack the repository into AI-friendly format.

        Args:
            repo_dir: Path to cloned repository

        Returns:
            Packed repository content as string

        Raises:
            subprocess.CalledProcessError: If repomix fails
        """
        result = subprocess.run(
            ["npx", "repomix", "--output", "-", "--style", "markdown"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def analyze(
        self, repo_url: HttpUrl, force_refresh: bool = False
    ) -> dict[str, Any]:
        """Analyze a GitHub repository.

        Args:
            repo_url: GitHub repository URL
            force_refresh: Force fresh clone even if cached

        Returns:
            Dictionary with repository analysis:
                - url: Repository URL
                - packed_content: Repomix output
                - repo_dir: Path to cloned repository
                - metadata: Additional repository metadata

        Raises:
            subprocess.CalledProcessError: If git or repomix fails
        """
        repo_url_str = str(repo_url)
        repo_hash = self._get_repo_hash(repo_url_str)
        repo_dir = self.cache_dir / repo_hash

        # Clone repository if not cached or force refresh
        if not repo_dir.exists() or force_refresh:
            if repo_dir.exists():
                # Remove existing directory for fresh clone
                subprocess.run(["rm", "-rf", str(repo_dir)], check=True)

            repo_dir.mkdir(parents=True, exist_ok=True)
            self._clone_repo(repo_url_str, repo_dir)

        # Run repomix to pack the repository
        packed_content = self._run_repomix(repo_dir)

        # Extract repository metadata
        repo_name = repo_url_str.rstrip("/").split("/")[-1]
        repo_owner = repo_url_str.rstrip("/").split("/")[-2]

        # Check for package.json or README for additional context
        metadata: dict[str, Any] = {
            "name": repo_name,
            "owner": repo_owner,
            "url": repo_url_str,
        }

        # Try to extract package.json metadata (Node.js projects)
        package_json_path = repo_dir / "package.json"
        if package_json_path.exists():
            with open(package_json_path) as f:
                package_data = json.load(f)
                metadata["package_name"] = package_data.get("name", repo_name)
                metadata["description"] = package_data.get("description", "")
                metadata["version"] = package_data.get("version", "")
                metadata["homepage"] = package_data.get("homepage", "")

        # Try to extract README excerpt (first 500 chars)
        for readme_name in ["README.md", "README.txt", "README"]:
            readme_path = repo_dir / readme_name
            if readme_path.exists():
                with open(readme_path) as f:
                    readme_content = f.read()
                    metadata["readme_excerpt"] = readme_content[:500]
                break

        return {
            "url": repo_url_str,
            "packed_content": packed_content,
            "repo_dir": str(repo_dir),
            "metadata": metadata,
        }

    def cleanup(self, repo_url: HttpUrl) -> None:
        """Remove cached repository clone.

        Args:
            repo_url: GitHub repository URL
        """
        repo_hash = self._get_repo_hash(str(repo_url))
        repo_dir = self.cache_dir / repo_hash

        if repo_dir.exists():
            subprocess.run(["rm", "-rf", str(repo_dir)], check=True)
