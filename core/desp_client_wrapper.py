from core.config import logger


class APIClientWrapper:
    def __init__(self, client):
        self.client = client
        self.api_calls = 0

    def _log_api_call(self, method_name, *args, **kwargs):
        """ Log API call with its name and parameters """
        self.api_calls += 1
        logger.info(f"API call number {self.api_calls}: {method_name}" +
                    (f", args: {args}" if args else "") +
                    (f", kwargs: {kwargs}" if kwargs else ""))

    def __getattr__(self, name):
        # Override the method to intercept API calls
        if hasattr(self.client, name) and callable(getattr(self.client, name)):
            method = getattr(self.client, name)

            def wrapper(*args, **kwargs):
                self._log_api_call(name, *args, **kwargs)
                return method(*args, **kwargs)

            return wrapper
        else:
            raise AttributeError(f"'{type(self.client).__name__}' object has no attribute '{name}'")
