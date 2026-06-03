# -*- coding: utf-8 -*-
"""GitHub Actions integration endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from api.v1.schemas.github_actions import (
    DispatchGitHubActionsRequest,
    DispatchGitHubActionsResponse,
    GitHubActionsStatusResponse,
)
from src.services.github_actions_service import (
    GitHubActionsConfigError,
    GitHubActionsRequestError,
    GitHubActionsService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _service() -> GitHubActionsService:
    return GitHubActionsService()


@router.get("/status", response_model=GitHubActionsStatusResponse)
def get_github_actions_status() -> GitHubActionsStatusResponse:
    try:
        return GitHubActionsStatusResponse.model_validate(_service().get_status())
    except GitHubActionsConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "github_actions_config_missing",
                "message": str(exc),
            },
        )
    except GitHubActionsRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_actions_request_failed",
                "message": str(exc),
                "status_code": exc.status_code,
            },
        )
    except Exception as exc:
        logger.error("Failed to load GitHub Actions status: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to load GitHub Actions status",
            },
        )


@router.post("/dispatch", response_model=DispatchGitHubActionsResponse)
def dispatch_github_actions(request: DispatchGitHubActionsRequest) -> DispatchGitHubActionsResponse:
    try:
        return DispatchGitHubActionsResponse.model_validate(
            _service().dispatch_workflow(mode=request.mode, force_run=request.force_run)
        )
    except GitHubActionsConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "github_actions_config_missing",
                "message": str(exc),
            },
        )
    except GitHubActionsRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "github_actions_request_failed",
                "message": str(exc),
                "status_code": exc.status_code,
            },
        )
    except Exception as exc:
        logger.error("Failed to dispatch GitHub Actions workflow: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to dispatch GitHub Actions workflow",
            },
        )

