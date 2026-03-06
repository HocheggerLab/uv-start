import os
import subprocess
from pathlib import Path

from rich import print as rprint

from uv_init.config import clean_env
from uv_init.exceptions import GitSetupError


def setup_git_repo(
    project_name: str,
    project_path: Path,
    private: bool = False,
) -> None:
    """Initialize git repo and optionally set up GitHub remote.

    Authentication is handled by the gh CLI, which uses credentials
    from `gh auth login`. If GH_TOKEN or GITHUB_TOKEN is set in the
    shell environment, it will be passed through to gh automatically.
    """
    repo_name = project_name
    try:
        # Create initial commit.
        # Pre-commit hooks (e.g. end-of-file-fixer) may auto-fix
        # staged files and abort the first commit with exit code 1.
        # The fixes persist in the working tree, so we re-stage and
        # commit again — exactly like doing it manually.
        subprocess.run(
            ["git", "add", "."],
            check=True,
            cwd=project_path,
            env=clean_env(),
        )
        first = subprocess.run(
            ["git", "commit", "-m", "chore: initial commit"],
            cwd=project_path,
            env=clean_env(),
        )
        if first.returncode != 0:
            subprocess.run(
                ["git", "add", "."],
                check=True,
                cwd=project_path,
                env=clean_env(),
            )
            subprocess.run(
                ["git", "commit", "-m", "chore: initial commit"],
                check=True,
                cwd=project_path,
                env=clean_env(),
            )

        # Prepare environment for gh command
        # Remove any stale GH_TOKEN/GITHUB_TOKEN that could override
        # gh auth login credentials. Only pass through if explicitly set.
        env = clean_env()
        github_token = os.environ.get("GH_TOKEN") or os.environ.get(
            "GITHUB_TOKEN"
        )
        if github_token:
            env["GH_TOKEN"] = github_token
        else:
            env.pop("GH_TOKEN", None)
            env.pop("GITHUB_TOKEN", None)

        # Create GitHub repository
        # gh CLI uses stored credentials from 'gh auth login'
        # unless GH_TOKEN is set in the environment
        visibility = "--private" if private else "--public"
        create_repo_cmd = [
            "gh",
            "repo",
            "create",
            repo_name,
            visibility,
            "--source",
            ".",
            "--remote",
            "origin",
            "--push",
        ]

        subprocess.run(
            create_repo_cmd,
            check=True,
            cwd=project_path,
            env=env,
        )

        rprint(
            f"[green]GitHub repository {repo_name} created and configured successfully[/green]"
        )

    except subprocess.CalledProcessError as e:
        raise GitSetupError(f"Failed to set up git repository: {e}") from e
