from fastapi import HTTPException, status


class RoleNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )


class RoleCreationFailedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create role",
        )


class RoleUpdateFailedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update role",
        )


class RoleDeletionFailedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete role",
        )
