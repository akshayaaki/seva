"""
Janseva AI — Authentication Routes
Register, login, profile management using Supabase Auth.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.database import get_supabase_admin, get_supabase_client
from app.auth import get_current_user, CurrentUser
from app.models.schemas import (
    RegisterRequest, LoginRequest, AuthResponse, ProfileResponse, MessageResponse
)
from app.services.audit import get_audit_service
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user (citizen by default)."""
    supabase = get_supabase_admin()
    audit = get_audit_service()

    try:
        # Create auth user in Supabase
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Email may already be in use.",
            )

        user_id = auth_response.user.id

        # Create user profile
        profile_data = {
            "id": user_id,
            "role": request.role if request.role in ["citizen"] else "citizen",
            "full_name": request.full_name,
            "phone": request.phone,
            "municipality_id": request.municipality_id,
        }

        supabase.table("user_profiles").insert(profile_data).execute()

        # If citizen role, create citizen record
        if request.role == "citizen":
            supabase.table("citizens").insert({
                "user_id": user_id,
            }).execute()

        await audit.log(
            action="user_registered",
            entity_type="user",
            entity_id=user_id,
            new_value={"email": request.email, "role": request.role},
        )

        logger.info("user_registered", user_id=user_id, role=request.role)

        return AuthResponse(
            access_token=auth_response.session.access_token if auth_response.session else "",
            refresh_token=auth_response.session.refresh_token if auth_response.session else "",
            user={
                "id": user_id,
                "email": request.email,
                "role": request.role,
                "full_name": request.full_name,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("registration_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    supabase = get_supabase_client()

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Get profile
        admin = get_supabase_admin()
        profile = (
            admin.table("user_profiles")
            .select("*")
            .eq("id", auth_response.user.id)
            .single()
            .execute()
        )

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "role": profile.data.get("role", "citizen") if profile.data else "citizen",
                "full_name": profile.data.get("full_name", "") if profile.data else "",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user's profile."""
    supabase = get_supabase_admin()
    profile = (
        supabase.table("user_profiles")
        .select("*")
        .eq("id", current_user.id)
        .single()
        .execute()
    )

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        role=profile.data["role"],
        full_name=profile.data["full_name"],
        phone=profile.data.get("phone"),
        municipality_id=profile.data.get("municipality_id"),
        department_id=profile.data.get("department_id"),
        ward_id=profile.data.get("ward_id"),
        preferred_language=profile.data.get("preferred_language", "en"),
        created_at=profile.data.get("created_at"),
    )


@router.put("/profile", response_model=MessageResponse)
async def update_profile(
    updates: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update current user's profile (allowed fields only)."""
    allowed_fields = {"full_name", "phone", "preferred_language", "ward_id"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    supabase = get_supabase_admin()
    supabase.table("user_profiles").update(filtered).eq("id", current_user.id).execute()

    return MessageResponse(message="Profile updated successfully")
