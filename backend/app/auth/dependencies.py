"""
Janseva AI — Authentication & Authorization
Handles JWT verification, user extraction, and role-based access control.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from app.database import get_supabase_admin
import structlog

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    CITIZEN = "citizen"
    WORKER = "worker"
    SUPERVISOR = "supervisor"
    DEPARTMENT_OFFICER = "department_officer"
    MUNICIPAL_ADMIN = "municipal_admin"
    SYSTEM_ADMIN = "system_admin"


class CurrentUser(BaseModel):
    """Authenticated user context extracted from JWT."""
    id: str
    email: str
    role: UserRole
    full_name: str
    municipality_id: Optional[str] = None
    department_id: Optional[str] = None
    ward_id: Optional[str] = None
    is_active: bool = True


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    Extract and verify the current user from the Supabase JWT.
    Returns a CurrentUser with role information from user_profiles.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    supabase = get_supabase_admin()

    try:
        # Verify the JWT with Supabase
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        auth_user = user_response.user

        # Fetch user profile with role
        profile_response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("id", auth_user.id)
            .single()
            .execute()
        )

        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found. Please complete registration.",
            )

        profile = profile_response.data

        if not profile.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return CurrentUser(
            id=auth_user.id,
            email=auth_user.email,
            role=UserRole(profile["role"]),
            full_name=profile["full_name"],
            municipality_id=profile.get("municipality_id"),
            department_id=profile.get("department_id"),
            ward_id=profile.get("ward_id"),
            is_active=profile.get("is_active", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("auth_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """Extract user if Bearer token is provided, or return None for public routes."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except Exception:
        return None


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory that enforces role-based access control.
    Usage: Depends(require_role(UserRole.MUNICIPAL_ADMIN, UserRole.SYSTEM_ADMIN))
    """
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return role_checker


def require_same_municipality(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Dependency that ensures user has a municipality assigned."""
    if not current_user.municipality_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No municipality assigned to your account",
        )
    return current_user


# Convenience dependencies
require_citizen = require_role(UserRole.CITIZEN)
require_worker = require_role(UserRole.WORKER)
require_supervisor = require_role(UserRole.SUPERVISOR, UserRole.DEPARTMENT_OFFICER, UserRole.MUNICIPAL_ADMIN, UserRole.SYSTEM_ADMIN)
require_department_officer = require_role(UserRole.DEPARTMENT_OFFICER, UserRole.MUNICIPAL_ADMIN, UserRole.SYSTEM_ADMIN)
require_admin = require_role(UserRole.MUNICIPAL_ADMIN, UserRole.SYSTEM_ADMIN)
require_system_admin = require_role(UserRole.SYSTEM_ADMIN)
