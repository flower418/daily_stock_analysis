# -*- coding: utf-8 -*-
"""Schemas for GitHub Actions integration."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class GitHubActionsRunSummary(BaseModel):
    id: int
    name: str = ""
    event: str = ""
    status: str = ""
    conclusion: Optional[str] = None
    display_title: str = ""
    head_branch: str = ""
    head_sha: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    run_started_at: Optional[str] = None
    html_url: str = ""


class GitHubActionsStatusResponse(BaseModel):
    configured: bool
    repo: str
    workflow: str
    branch: str
    workflow_state: str = ""
    workflow_url: str = ""
    runs: List[GitHubActionsRunSummary] = Field(default_factory=list)


class DispatchGitHubActionsRequest(BaseModel):
    mode: Literal["full", "market-only", "stocks-only"] = "full"
    force_run: bool = False


class DispatchGitHubActionsResponse(BaseModel):
    success: bool
    message: str
    repo: str
    workflow: str
    branch: str
    mode: str
    force_run: bool

