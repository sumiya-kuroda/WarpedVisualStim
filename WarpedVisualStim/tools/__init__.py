class OperationError(Exception):
    """Custom exception for operation-related errors."""
    def __init__(self, message):
        super().__init__(message)