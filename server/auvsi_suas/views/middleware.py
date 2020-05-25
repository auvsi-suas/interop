"""Views middleware."""

import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(object):
    """Logging middleware for custom request/response logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        req_logger = None
        if response.status_code < 400:
            req_logger = logger.info
        elif response.status_code < 500:
            req_logger = logger.warning
        else:
            req_logger = logger.error

        delta_time = '%.4fs' % (time.time() - start_time)
        req_logger('[%d] %s (%s)\n>>>\n%s\n===\n%s\n<<<', response.status_code,
                   request.get_full_path(), delta_time,
                   str(request), str(response))

        return response
