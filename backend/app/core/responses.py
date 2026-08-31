from typing import Any

from fastapi.encoders import jsonable_encoder


def success_response(message: str, data: Any | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": True,
        "message": message,
    }

    if data is not None:
        response["data"] = jsonable_encoder(data)

    return response
