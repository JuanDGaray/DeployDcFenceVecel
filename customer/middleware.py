from .presence import touch_last_activity


class LastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        touch_last_activity(request)
        return self.get_response(request)
