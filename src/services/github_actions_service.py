# -*- coding: utf-8 -*-
"""GitHub Actions integration service for local Web/Desktop UI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class GitHubActionsConfigError(Exception):
    """Raised when GitHub Actions integration config is incomplete."""


class GitHubActionsRequestError(Exception):
    """Raised when GitHub API returns an error."""

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class GitHubActionsSettings:
    repo: str
    token: str
    workflow: str
    branch: str


class GitHubActionsService:
    """Call GitHub Actions APIs using local `.env` credentials."""

    def __init__(self, manager: Optional[ConfigManager] = None) -> None:
        self._manager = manager or ConfigManager()

    def _settings(self) -> GitHubActionsSettings:
        config = {key.upper(): value for key, value in self._manager.read_config_map().items()}
        repo = (config.get("GITHUB_ACTIONS_REPO") or "").strip()
        token = (config.get("GITHUB_ACTIONS_TOKEN") or "").strip()
        workflow = (config.get("GITHUB_ACTIONS_WORKFLOW") or "00-daily-analysis.yml").strip()
        branch = (config.get("GITHUB_ACTIONS_BRANCH") or "main").strip()
        if not repo or "/" not in repo:
            raise GitHubActionsConfigError("GITHUB_ACTIONS_REPO must be set as owner/repo")
        if not token:
            raise GitHubActionsConfigError("GITHUB_ACTIONS_TOKEN is required")
        if not workflow:
            raise GitHubActionsConfigError("GITHUB_ACTIONS_WORKFLOW is required")
        return GitHubActionsSettings(repo=repo, token=token, workflow=workflow, branch=branch or "main")

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(
        self,
        method: str,
        url: str,
        *,
        settings: GitHubActionsSettings,
        timeout_seconds: float = 20.0,
        **kwargs: Any,
    ) -> requests.Response:
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(settings.token),
                timeout=timeout_seconds,
                **kwargs,
            )
        except requests.RequestException as exc:
            logger.warning("GitHub Actions request failed: %s", exc)
            raise GitHubActionsRequestError(f"GitHub API request failed: {exc}") from exc

        if response.status_code >= 400:
            message = response.text.strip() or response.reason or "GitHub API request failed"
            raise GitHubActionsRequestError(message, status_code=response.status_code)
        return response

    @staticmethod
    def _format_time(value: Any) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return str(value)

    @classmethod
    def _run_summary(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": item.get("id"),
            "name": item.get("name") or "",
            "event": item.get("event") or "",
            "status": item.get("status") or "",
            "conclusion": item.get("conclusion"),
            "display_title": item.get("display_title") or item.get("name") or "",
            "head_branch": item.get("head_branch") or "",
            "head_sha": item.get("head_sha") or "",
            "created_at": cls._format_time(item.get("created_at")),
            "updated_at": cls._format_time(item.get("updated_at")),
            "run_started_at": cls._format_time(item.get("run_started_at")),
            "html_url": item.get("html_url") or "",
        }

    def get_status(self, *, limit: int = 10) -> Dict[str, Any]:
        settings = self._settings()
        workflow_url = (
            f"https://api.github.com/repos/{settings.repo}/actions/workflows/{settings.workflow}"
        )
        workflow = self._request("GET", workflow_url, settings=settings).json()
        runs_url = f"{workflow_url}/runs"
        runs_payload = self._request(
            "GET",
            runs_url,
            settings=settings,
            params={"per_page": max(1, min(limit, 30))},
        ).json()
        return {
            "configured": True,
            "repo": settings.repo,
            "workflow": settings.workflow,
            "branch": settings.branch,
            "workflow_state": workflow.get("state") or "",
            "workflow_url": workflow.get("html_url") or "",
            "runs": [self._run_summary(item) for item in runs_payload.get("workflow_runs", [])],
        }

    def dispatch_workflow(self, *, mode: str = "full", force_run: bool = False) -> Dict[str, Any]:
        settings = self._settings()
        normalized_mode = mode if mode in {"full", "market-only", "stocks-only"} else "full"
        url = f"https://api.github.com/repos/{settings.repo}/actions/workflows/{settings.workflow}/dispatches"
        self._request(
            "POST",
            url,
            settings=settings,
            json={
                "ref": settings.branch,
                "inputs": {
                    "mode": normalized_mode,
                    "force_run": "true" if force_run else "false",
                },
            },
        )
        return {
            "success": True,
            "message": "GitHub Actions workflow dispatch submitted",
            "repo": settings.repo,
            "workflow": settings.workflow,
            "branch": settings.branch,
            "mode": normalized_mode,
            "force_run": force_run,
        }

