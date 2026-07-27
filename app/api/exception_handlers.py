import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config.settings import settings
from app.core.exceptions.token import TokenException
from app.domain.exceptions.base import DomainException

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request, exc: DomainException | TokenException
) -> JSONResponse:
    """
    Единая точка перевода доменных/токен-ошибок в HTTP-ответы.

    TokenException (app/core/exceptions/token.py) — технические ошибки
    аутентификации, не относящиеся к домену, но с той же формой
    (message/status_code), поэтому обрабатываются тем же handler'ом.
    """
    log_level = logging.WARNING if exc.status_code >= 500 else logging.INFO
    logger.log(
        log_level,
        "Domain exception on %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Ошибки валидации входных Pydantic-схем (тело запроса, query-параметры).

    FastAPI по умолчанию уже отдаёт 422 с похожим форматом, но со своим
    ключом "detail" -> list[dict]. Переопределяем явно, чтобы формат был
    предсказуемым и одинаковым с domain_exception_handler ({"detail": ...}),
    и чтобы при желании было куда добавить логирование/маппинг полей.
    """
    logger.info(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Последняя линия защиты — любое исключение, не пойманное явно нигде
    (баг, обрыв соединения с БД, что угодно непредвиденное).

    В dev/test показываем текст ошибки для удобства отладки. В проде —
    НИКОГДА: детали исключения (пути к файлам, куски SQL, внутренние
    структуры) не должны утекать наружу. Полный трейсбек в любом случае
    уходит в лог через logger.exception, независимо от окружения.
    """
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )

    detail = str(exc) if not settings.is_prod else "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Вызывается один раз при старте приложения, см. app/main.py."""
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(TokenException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)