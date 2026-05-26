from googleapiclient.errors import HttpError # google
from dataclasses import dataclass # stdlib
from typing import Callable # stdlib

@dataclass(frozen=True)
class FlintError:
    code: int | None
    message: str

def wrap_exceptions[**P, T](func: Callable[P, T]) -> Callable[P, tuple[FlintError | None, T | None]]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> tuple[FlintError | None, T | None]:
        try: return None, func(*args, **kwargs)
        except HttpError as err: return FlintError(err.status_code, err.reason), None
        except Exception as err: return FlintError(None, str(err)), None

    return wrapper