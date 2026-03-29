



class DomainException(Exception):
    """Базовый класс для всех исключений в доменной логике."""
    
    message: str = "Произошла ошибка в доменной логике."
    status_code: int = 400  # HTTP статус по умолчанию для ошибок домена


    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)