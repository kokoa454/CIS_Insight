class AIServiceError(Exception):
    """基底クラス"""
    def __init__(self, message="Unknown error"):
        self.user_message = message
        super().__init__(message)

class RateLimitError(AIServiceError):
    def __init__(self):
        super().__init__("Rate limit hit")

class AuthenticationError(AIServiceError):
    def __init__(self):
        super().__init__("Authentication error")

class ModelNotFoundError(AIServiceError):
    def __init__(self):
        super().__init__("Model not found error")

class ServerError(AIServiceError):
    def __init__(self):
        super().__init__("Request error")

class NetworkError(AIServiceError):
    def __init__(self):
        super().__init__("Network error")


def convert_to_custom_ai_exception(e: Exception) -> AIServiceError:
    status_code = getattr(e, 'status_code', getattr(e, 'code', None))
    
    if status_code == 429: 
        return RateLimitError()
    if status_code in [401, 403]: 
        return AuthenticationError()
    if status_code == 404: 
        return ModelNotFoundError()
    if status_code in [500, 503]: 
        return ServerError()
        
    error_str = str(e).lower()
    if "network" in error_str or "connection" in error_str: 
        return NetworkError()
        
    return AIServiceError()