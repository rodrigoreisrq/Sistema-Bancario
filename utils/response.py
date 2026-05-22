from fastapi.responses import JSONResponse

def success(data=None, message="Operação realizada com sucesso", status_code=200):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "message": message,
            "data": data
        }
    )

def error(message="Erro inesperado", status_code=400):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "message": message,
            "data": None
        }
    )