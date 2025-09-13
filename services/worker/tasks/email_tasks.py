"""
Email-related Celery tasks for Ghostworks Worker.
Handles user notifications, verification emails, and system alerts.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from celery import current_task
import structlog

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ..celery_app import celery_app
from ..database import get_database_session
from ..telemetry import get_tracer, worker_telemetry
from ..metrics import worker_metrics, track_task_metric
from packages.shared.src.logging_config import get_logger, with_operation, log_context

logger = get_logger(__name__)
tracer = get_tracer(__name__)


@celery_app.task(bind=True, name="send_verification_email")
@track_task_metric("email_task", task_type="verification")
def send_verification_email(self, user_id: str, email: str, verification_token: str):
    """
    Send email verification to new user.
    
    Args:
        user_id: UUID of the user
        email: User's email address
        verification_token: Verification token for email confirmation
    """
    with tracer.start_as_current_span("email.send_verification") as span:
        # Add span attributes
        span.set_attribute("task.id", current_task.request.id)
        span.set_attribute("user.id", user_id)
        span.set_attribute("email.type", "verification")
        span.set_attribute("email.recipient", email)
        
        # Use log context for structured logging
        with log_context(
            user_id=user_id,
            operation="email.send_verification",
            email_type="verification",
            email_recipient=email
        ):
            try:
                logger.info(
                    "Sending verification email",
                    email=email,
                )
            
                # TODO: Implement actual email sending logic
                # For now, just log the action
                logger.info(
                    "Verification email sent successfully",
                    email=email,
                )
                
                # Record successful email task
                worker_telemetry.record_email_task("verification", success=True)
                worker_metrics.record_email_task("verification", "success")
                span.set_attribute("email.success", True)
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "email": email,
                    "message": "Verification email sent"
                }
            
            except Exception as e:
                # Record failed email task
                worker_telemetry.record_email_task("verification", success=False)
                worker_metrics.record_email_task("verification", "failure")
                span.set_attribute("email.success", False)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to send verification email",
                    email=email,
                    error=str(e),
                    exc_info=True,
                )
                
                # Retry with exponential backoff
                raise self.retry(
                    exc=e,
                    countdown=60 * (2 ** self.request.retries),
                    max_retries=3
                )


@celery_app.task(bind=True, name="send_password_reset_email")
@track_task_metric("email_task", task_type="password_reset")
def send_password_reset_email(self, user_id: str, email: str, reset_token: str):
    """
    Send password reset email to user.
    
    Args:
        user_id: UUID of the user
        email: User's email address
        reset_token: Password reset token
    """
    with log_context(
        user_id=user_id,
        operation="email.send_password_reset",
        email_type="password_reset",
        email_recipient=email
    ):
        try:
            logger.info(
                "Sending password reset email",
                email=email,
            )
            
            # TODO: Implement actual email sending logic
            # For now, just log the action
            logger.info(
                "Password reset email sent successfully",
                email=email,
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "email": email,
                "message": "Password reset email sent"
            }
            
        except Exception as e:
            logger.error(
                "Failed to send password reset email",
                email=email,
                error=str(e),
                exc_info=True,
            )
            
            # Retry with exponential backoff
            raise self.retry(
                exc=e,
                countdown=60 * (2 ** self.request.retries),
                max_retries=3
            )


@celery_app.task(bind=True, name="send_workspace_invitation")
@track_task_metric("email_task", task_type="workspace_invitation")
def send_workspace_invitation(self, inviter_id: str, invitee_email: str, workspace_name: str, invitation_token: str):
    """
    Send workspace invitation email.
    
    Args:
        inviter_id: UUID of the user sending the invitation
        invitee_email: Email of the user being invited
        workspace_name: Name of the workspace
        invitation_token: Invitation token for accepting the invite
    """
    with log_context(
        user_id=inviter_id,
        operation="email.send_workspace_invitation",
        email_type="workspace_invitation",
        email_recipient=invitee_email,
        workspace_name=workspace_name
    ):
        try:
            logger.info(
                "Sending workspace invitation",
                invitee_email=invitee_email,
                workspace_name=workspace_name,
            )
            
            # TODO: Implement actual email sending logic
            # For now, just log the action
            logger.info(
                "Workspace invitation sent successfully",
                invitee_email=invitee_email,
                workspace_name=workspace_name,
            )
            
            return {
                "status": "success",
                "inviter_id": inviter_id,
                "invitee_email": invitee_email,
                "workspace_name": workspace_name,
                "message": "Workspace invitation sent"
            }
            
        except Exception as e:
            logger.error(
                "Failed to send workspace invitation",
                invitee_email=invitee_email,
                workspace_name=workspace_name,
                error=str(e),
                exc_info=True,
            )
            
            # Retry with exponential backoff
            raise self.retry(
                exc=e,
                countdown=60 * (2 ** self.request.retries),
                max_retries=3
            )