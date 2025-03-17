from app.exceptions.auth import SignInFailureException, UserIsUnactiveException
from app.helpers.auth import verify_password
from app.schemas.users import CreateUserQueryResponse, UserMembershipQueryReponse


def verify_user_status(user: CreateUserQueryResponse | UserMembershipQueryReponse | None) -> None:
    if user is None:
        raise SignInFailureException()

    if user.is_active is False:
        raise UserIsUnactiveException()

    if user.deleted_at is not None:
        print(
            "user.deleted_at",
            user.username,
            user.email,
            user.deleted_at,
        )
        raise SignInFailureException()


def verify_user_password(
    password_input: str,
    password_hash: str,
) -> None:
    is_verified = verify_password(
        plain_password=password_input,
        hashed_password=password_hash,
    )

    if not is_verified:
        raise SignInFailureException()
