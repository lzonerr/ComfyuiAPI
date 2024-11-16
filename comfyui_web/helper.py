def success_response(data, message="Success"):
    return {
        "status": "success",
        "message": message,
        "data": data
    }, 200

def error_response(message="An error occurred"):
    return {
        "status": "error",
        "message": message
    }, 400

