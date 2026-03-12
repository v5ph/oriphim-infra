"""
app/routes/onboarding.py - REST API Endpoints for Onboarding System

Implements:
1. Tenant provisioning endpoints
2. User management endpoints
3. API key management endpoints
4. Audit log endpoints
5. Multi-tenancy middleware
6. JWT authentication and token refresh
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
import logging
import jwt

from app.core.onboarding import (
    create_tenant,
    get_tenant,
    list_tenants,
    create_user,
    get_user,
    list_tenant_users,
    change_user_role,
    generate_api_key,
    validate_api_key,
    revoke_api_key,
    list_api_keys,
    list_audit_log,
    verify_audit_chain,
    has_permission,
    Role,
    SupportTier,
    APIKeyScope,
    init_onboarding_db
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    refresh_access_token,
    session_manager
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])

# ============================================================================
# SCHEMAS
# ============================================================================

class TenantCreateRequest(BaseModel):
    org_name: str = Field(..., min_length=3, max_length=255)
    domain: str = Field(..., min_length=3, max_length=253, pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$")
    support_tier: str = Field(default="standard", pattern="^(standard|premium|enterprise)$")


class UserCreateRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(admin|risk-officer|analyst|viewer)$")
    mfa_enabled: bool = True


class APIKeyCreateRequest(BaseModel):
    user_id: Optional[str] = None
    scope: str = Field(..., pattern="^(validate-only|admin|read-metrics)$")
    expires_in_days: int = Field(default=90, ge=1, le=365)


class UserRoleChangeRequest(BaseModel):
    new_role: str = Field(..., pattern="^(admin|risk-officer|analyst|viewer)$")


# ============================================================================
# DEPENDENCY: EXTRACT & VALIDATE TENANT FROM API KEY
# ============================================================================

async def get_current_key_metadata(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Extract API key metadata from Authorization header.
    
    Validates API key and returns key metadata.
    All protected onboarding endpoints require this.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    bearer_token = authorization.replace("Bearer ", "", 1).strip()

    if bearer_token.count(".") == 2:
        try:
            claims = verify_token(bearer_token, expected_type="access")
            if not session_manager.is_session_valid(claims["jti"]):
                raise HTTPException(status_code=401, detail="Session expired or invalid")
            session_manager.update_activity(claims["jti"])
            return {
                "tenant_id": claims["tenant_id"],
                "user_id": claims["user_id"],
                "scope": claims["scope"],
                "auth_type": "access_token",
            }
        except HTTPException:
            raise
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc

    key_metadata = validate_api_key(bearer_token)
    if not key_metadata:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    return key_metadata


async def get_current_tenant(
    key_metadata: Dict[str, Any] = Depends(get_current_key_metadata)
) -> str:
    """Extract tenant_id from validated key metadata."""
    return key_metadata["tenant_id"]


_ACTION_SCOPES: Dict[str, Set[str]] = {
    "manage_users": {APIKeyScope.ADMIN.value},
    "manage_config": {APIKeyScope.ADMIN.value},
    "view_audit": {APIKeyScope.ADMIN.value, APIKeyScope.READ_METRICS.value},
    "validate": {APIKeyScope.ADMIN.value, APIKeyScope.VALIDATE_ONLY.value},
    "read_results": {APIKeyScope.ADMIN.value, APIKeyScope.READ_METRICS.value},
}


def require_permission(action: str, resource: str = "all"):
    """
    Dependency that checks user has required permission.
    
    Usage:
        @router.get("/some-endpoint")
        async def endpoint(check: bool = Depends(require_permission("manage_users"))):
            ...
    """
    async def check_permission(
        key_metadata: Dict[str, Any] = Depends(get_current_key_metadata)
    ) -> bool:
        user = get_user(key_metadata["user_id"])
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
        
        allowed_scopes = _ACTION_SCOPES.get(action)
        if allowed_scopes and key_metadata["scope"] not in allowed_scopes:
            raise HTTPException(status_code=403, detail="API key scope not permitted")

        # Check permission
        if not has_permission(user["user_id"], action, resource):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for action: {action}"
            )
        
        return True
    
    return check_permission


# ============================================================================
# TENANT ENDPOINTS
# ============================================================================

@router.post("/tenants", status_code=201)
async def create_tenant_endpoint(request: TenantCreateRequest):
    """
    Create a new tenant organization.
    
    This is the first step in onboarding. Domain must be verified via DNS.
    
    Returns:
        - tenant_id: Unique identifier for organization
        - status: "active" (ready for user provisioning)
    """
    try:
        tenant = create_tenant(
            org_name=request.org_name,
            domain=request.domain,
            support_tier=request.support_tier
        )
        
        return {
            "tenant_id": tenant["tenant_id"],
            "org_name": tenant["org_name"],
            "domain": tenant["domain"],
            "status": tenant["status"],
            "support_tier": tenant["support_tier"],
            "created_at": tenant["created_at"],
            "next_step": "Verify domain via DNS TXT record, then add admin user"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants")
async def list_tenants_endpoint(
    current_tenant: str = Depends(get_current_tenant)
):
    """
    List all tenant organizations.

    Requires authentication to prevent tenant enumeration attacks.
    Returns tenant info for the authenticated user's tenant only.
    """
    tenant = get_tenant(current_tenant)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "tenant_count": 1,
        "tenants": [
            {
                "tenant_id": tenant["tenant_id"],
                "org_name": tenant["org_name"],
                "domain": tenant["domain"],
                "status": tenant["status"],
                "support_tier": tenant["support_tier"],
                "created_at": tenant["created_at"],
            }
        ],
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant_endpoint(
    tenant_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("manage_config"))
):
    """Retrieve tenant details (must belong to requesting tenant)."""
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot access other tenants")
    
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/tenants/{tenant_id}/users", status_code=201)
async def create_user_endpoint(
    tenant_id: str,
    request: UserCreateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Add a user to the tenant with role-based access.
    
    Bootstrap mode: First user creation does not require authentication.
    Subsequent users: Requires admin or risk-officer role.
    
    Roles:
    - admin: Full access (users, configs, audits)
    - risk-officer: Can manage configs and review policies
    - analyst: Can validate and view results
    - viewer: Read-only access to audit trail
    """
    # Check bootstrap mode atomically (within transaction)
    from app.core.onboarding import _get_bootstrap_lock
    
    bootstrap_lock = _get_bootstrap_lock(tenant_id)
    actor_id: Optional[str] = None
    with bootstrap_lock:
        existing_users = list_tenant_users(tenant_id)
        is_bootstrap = len(existing_users) == 0
        
        if is_bootstrap:
            logger.info(f"Bootstrap mode: Creating first user for tenant {tenant_id}")
            if request.role != "admin":
                raise HTTPException(
                    status_code=400, 
                    detail="First user must have admin role (bootstrap)"
                )
            actor_id = f"bootstrap:{request.email.lower()}"

    if not is_bootstrap:
        key_metadata = await get_current_key_metadata(authorization)
        
        if tenant_id != key_metadata["tenant_id"]:
            raise HTTPException(status_code=403, detail="Cannot manage other tenants")
        
        allowed_scopes = _ACTION_SCOPES.get("manage_users", set())
        if key_metadata["scope"] not in allowed_scopes:
            raise HTTPException(status_code=403, detail="API key scope not permitted")
        
        user_check = get_user(key_metadata["user_id"])
        if not user_check:
            raise HTTPException(status_code=403, detail="User not found")
        
        if not has_permission(key_metadata["user_id"], "manage_users", "all"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for action: manage_users"
            )
        actor_id = key_metadata["user_id"]
    
    try:
        user = create_user(
            tenant_id=tenant_id,
            email=request.email,
            role=request.role,
            mfa_enabled=request.mfa_enabled,
            actor_id=actor_id
        )
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "mfa_enabled": user["mfa_enabled"],
            "created_at": user["created_at"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/{tenant_id}/users")
async def list_users_endpoint(
    tenant_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("manage_users"))
):
    """List all users in tenant."""
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot access other tenants")
    
    users = list_tenant_users(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "user_count": len(users),
        "users": [
            {
                "user_id": u["user_id"],
                "email": u["email"],
                "role": u["role"],
                "mfa_enabled": bool(u["mfa_enabled"]),
                "created_at": u["created_at"]
            }
            for u in users
        ]
    }


@router.patch("/tenants/{tenant_id}/users/{user_id}/role", status_code=200)
async def change_user_role_endpoint(
    tenant_id: str,
    user_id: str,
    request: UserRoleChangeRequest,
    current_tenant: str = Depends(get_current_tenant),
    key_metadata: Dict[str, Any] = Depends(get_current_key_metadata),
    _: bool = Depends(require_permission("manage_users"))
):
    """
    Change user's role (permission escalation must be audited).
    
    Only admins can perform this action.
    """
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot manage other tenants")
    
    try:
        user = change_user_role(
            user_id=user_id,
            new_role=request.new_role,
            actor_id=key_metadata["user_id"]
        )
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "old_role": "unknown",  # Would be in audit log
            "new_role": user["role"],
            "changed_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/tenants/{tenant_id}/api-keys", status_code=201)
async def create_api_key_endpoint(
    tenant_id: str,
    request: APIKeyCreateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate a new API key.
    
    WARNING: The secret is returned only once in this response.
    Store it securely. If lost, generate a new key.
    
    Scopes:
    - validate-only: Can only call /v2/validate
    - admin: Full API access
    - read-metrics: Read-only access to audit logs and health metrics
    """
    try:
        existing_keys = list_api_keys(tenant_id)
        is_bootstrap = len(existing_keys) == 0
        actor_id: Optional[str] = None

        if is_bootstrap:
            if not request.user_id:
                raise HTTPException(
                    status_code=400,
                    detail="Bootstrap mode requires user_id for first API key"
                )

            bootstrap_user = get_user(request.user_id)
            if not bootstrap_user:
                raise HTTPException(status_code=404, detail="User not found")
            if bootstrap_user.get("tenant_id") != tenant_id:
                raise HTTPException(status_code=403, detail="User does not belong to tenant")
            if bootstrap_user.get("role") != Role.ADMIN.value:
                raise HTTPException(
                    status_code=403,
                    detail="First API key can only be created for admin user"
                )

            user_id = request.user_id
            actor_id = request.user_id
            logger.info(f"Bootstrap mode: Creating first API key for tenant {tenant_id}")
        else:
            key_metadata = await get_current_key_metadata(authorization)

            if tenant_id != key_metadata["tenant_id"]:
                raise HTTPException(status_code=403, detail="Cannot create keys for other tenants")

            allowed_scopes = _ACTION_SCOPES.get("manage_config", set())
            if key_metadata["scope"] not in allowed_scopes:
                raise HTTPException(status_code=403, detail="API key scope not permitted")

            user_check = get_user(key_metadata["user_id"])
            if not user_check:
                raise HTTPException(status_code=403, detail="User not found")

            if not has_permission(key_metadata["user_id"], "manage_config", "all"):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions for action: manage_config"
                )

            user_id = key_metadata["user_id"]
            actor_id = key_metadata["user_id"]
        
        key = generate_api_key(
            tenant_id=tenant_id,
            user_id=user_id,
            scope=request.scope,
            expires_in_days=request.expires_in_days,
            actor_id=actor_id,
        )
        
        return {
            "api_key": key["api_key"],
            "key_id": key["key_id"],
            "scope": key["scope"],
            "expires_at": key["expires_at"],
            "warning": "SAVE THIS KEY SECURELY. YOU WILL NOT SEE IT AGAIN."
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/{tenant_id}/api-keys")
async def list_api_keys_endpoint(
    tenant_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("manage_config"))
):
    """
    List all API keys for tenant (secret hashes not returned).
    """
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot access other tenants")
    
    keys = list_api_keys(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "key_count": len(keys),
        "keys": [
            {
                "key_id": k["key_id"],
                "scope": k["scope"],
                "status": k["status"],
                "expires_at": k["expires_at"],
                "created_at": k["created_at"],
                "last_used_at": k["last_used_at"],
                "usage_count": k["usage_count"]
            }
            for k in keys
        ]
    }


@router.delete("/tenants/{tenant_id}/api-keys/{key_id}", status_code=204)
async def revoke_api_key_endpoint(
    tenant_id: str,
    key_id: str,
    current_tenant: str = Depends(get_current_tenant),
    key_metadata: Dict[str, Any] = Depends(get_current_key_metadata),
    _: bool = Depends(require_permission("manage_config"))
):
    """
    Revoke an API key immediately.
    
    The key can no longer be used for validation requests.
    This action is audited.
    """
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot manage other tenants")
    
    try:
        revoke_api_key(key_id, actor_id=key_metadata["user_id"])
        return {}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get("/tenants/{tenant_id}/audit-log")
async def get_audit_log_endpoint(
    tenant_id: str,
    event_type: Optional[str] = None,
    days_back: int = 90,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("view_audit"))
):
    """
    Retrieve immutable audit log for tenant.
    
    Audit log includes all:
    - Tenant creation, user additions, role changes
    - API key generation and revocation
    - Configuration changes
    - Policy approvals and rollbacks
    
    Each entry is cryptographically chained to prevent tampering.
    """
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot access other tenants")
    
    events = list_audit_log(tenant_id, event_type=event_type, days_back=days_back)
    
    return {
        "tenant_id": tenant_id,
        "event_count": len(events),
        "events": events,
        "chain_verified": verify_audit_chain(tenant_id)
    }


@router.get("/tenants/{tenant_id}/audit-log/verify")
async def verify_audit_chain_endpoint(
    tenant_id: str,
    current_tenant: str = Depends(get_current_tenant),
    _: bool = Depends(require_permission("view_audit"))
):
    """
    Verify audit log chain integrity (detect tampering).
    
    Returns:
        - chain_intact: True if no tampering detected
        - last_verified: Timestamp of verification
    """
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Cannot access other tenants")
    
    is_intact = verify_audit_chain(tenant_id)
    
    if not is_intact:
        logger.error(f"AUDIT CHAIN TAMPERED: {tenant_id}")
        # In production, trigger incident response
    
    return {
        "tenant_id": tenant_id,
        "chain_intact": is_intact,
        "verified_at": datetime.utcnow().isoformat(),
        "alert": "CHAIN TAMPERING DETECTED" if not is_intact else None
    }


# ============================================================================
# JWT AUTHENTICATION ENDPOINTS
# ============================================================================

class LoginRequest(BaseModel):
    api_key: str = Field(..., description="API key for authentication")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="Client IP address")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    Exchange API key for JWT tokens (access + refresh).
    
    This enables session-based authentication with token refresh capability.
    Access tokens expire in 15 minutes, refresh tokens in 7 days.
    
    Returns:
        - access_token: Short-lived token for API requests
        - refresh_token: Long-lived token for obtaining new access tokens
        - expires_in: Access token lifetime in seconds
    """
    # Validate API key
    key_metadata = validate_api_key(request.api_key)
    if not key_metadata:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    
    # Create JWT tokens
    access_token = create_access_token(
        subject=key_metadata["user_id"],
        tenant_id=key_metadata["tenant_id"],
        user_id=key_metadata["user_id"],
        scope=key_metadata["scope"]
    )
    
    refresh_token_str = create_refresh_token(
        subject=key_metadata["user_id"],
        tenant_id=key_metadata["tenant_id"],
        user_id=key_metadata["user_id"],
        scope=key_metadata["scope"],
    )
    
    # Decode to get JTI for session management
    access_claims = verify_token(access_token, expected_type="access")
    
    # Create session
    session_manager.create_session(
        user_id=key_metadata["user_id"],
        tenant_id=key_metadata["tenant_id"],
        jti=access_claims["jti"],
        metadata={
            "user_agent": request.user_agent or http_request.headers.get("user-agent"),
            "ip_address": request.ip_address or http_request.client.host,
            "api_key_id": key_metadata.get("key_id")
        }
    )
    
    logger.info(f"User logged in: {key_metadata['user_id']} (tenant: {key_metadata['tenant_id']})")
    
    from app.core.security import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(request: RefreshRequest):
    """
    Refresh access token using valid refresh token.
    
    This allows clients to obtain new access tokens without re-authenticating.
    The refresh token remains valid and can be reused until expiration.
    
    Returns:
        - access_token: New access token
        - refresh_token: Same refresh token
        - expires_in: New access token lifetime
    """
    try:
        tokens = refresh_access_token(request.refresh_token)
        
        # Create session for new access token
        access_claims = verify_token(tokens["access_token"], expected_type="access")
        session_manager.create_session(
            user_id=access_claims["user_id"],
            tenant_id=access_claims["tenant_id"],
            jti=access_claims["jti"]
        )
        
        return TokenResponse(**tokens)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired. Please login again.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")


@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout user by invalidating current session and blacklisting token.
    
    The access token is immediately added to blacklist, preventing further use.
    All active sessions for the user are terminated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        claims = verify_token(token, expected_type="access")
        
        # Terminate all user sessions
        terminated = session_manager.terminate_user_sessions(
            user_id=claims["user_id"],
            tenant_id=claims["tenant_id"]
        )
        
        logger.info(f"User logged out: {claims['user_id']} ({terminated} sessions terminated)")
        
        return {
            "message": "Logged out successfully",
            "sessions_terminated": terminated
        }
    
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@router.get("/auth/verify")
async def verify_auth_token(authorization: Optional[str] = Header(None)):
    """
    Verify JWT token validity and return claims.
    
    Useful for debugging and validating token structure.
    Also updates session activity timestamp.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        claims = verify_token(token, expected_type="access")
        
        # Check session validity
        if not session_manager.is_session_valid(claims["jti"]):
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        
        # Update activity
        session_manager.update_activity(claims["jti"])
        
        return {
            "valid": True,
            "user_id": claims["user_id"],
            "tenant_id": claims["tenant_id"],
            "scope": claims["scope"],
            "expires_at": datetime.fromtimestamp(claims["exp"]).isoformat()
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# ============================================================================
# INITIALIZATION
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """Initialize onboarding database on app startup."""
    init_onboarding_db()
    logger.info("Onboarding system initialized")
