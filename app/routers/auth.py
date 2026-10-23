
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.utils.security import verify_password, create_access_token


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    """

    # Find user by email
    user = (
        db.query(User)
        .filter(User.email == str(data.email).lower())
        .first()
    )

    # Check credentials
    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check whether the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    # Generate JWT token
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    # Return token and user information
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )
