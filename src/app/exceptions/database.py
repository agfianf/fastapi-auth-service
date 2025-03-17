from fastapi import HTTPException, status


# Custom exception for database errors


class DataNotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data not found: {str(detail)}")


class DataAlreadyExistsException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Data already exists: {str(detail)}")


class DataNotNullException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Data cannot be null: {str(detail)}")


class DataDuplicateException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Data duplicate: {str(detail)}")


class DataOperationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data operation failed: {str(detail)}"
        )


class DatabaseException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(detail)}")
