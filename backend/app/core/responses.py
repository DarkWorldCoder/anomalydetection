from typing import Any 
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

def create_response(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    response_content = {
        "message": message,
        "success": status_code < 400
    }
    if data is not None:
        response_content["data"] = jsonable_encoder(data)
    return JSONResponse(content=jsonable_encoder(response_content), status_code=status_code)