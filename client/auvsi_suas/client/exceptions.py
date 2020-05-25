"""Custom client exception types."""

import requests


class InteropError(requests.HTTPError):
    """The interop server reported an error."""
    def __init__(self, response):
        """Create an InteropError.

        Args:
            response: requests.Response object that indicated the error.
        """
        message = '{method} {url} -> {code} Error ({reason}): {message}'
        message = message.format(method=response.request.method,
                                 url=response.request.url,
                                 code=response.status_code,
                                 reason=response.reason,
                                 message=response.text)

        super(InteropError, self).__init__(message, response=response)
