from django.http import HttpResponse
import json


class NonHtmlDebugToolbarMiddleware(object):
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any non-HTML response in HTML if the request has a
    'debug' query parameter (e.g. http://localhost/foo?debug) Special handling
    for json (pretty printing) and binary data (only show data length).

    Based on http://stackoverflow.com/a/19249559/10817
    """
    @staticmethod
    def process_response(request, response):
        if request.GET.get('debug') == '':
            if response['Content-Type'] == 'application/octet-stream':
                new_content = '<html><body>Binary Data, ' \
                    'Length: {}</body></html>'.format(len(response.content))
                response = HttpResponse(new_content)
            elif not response['Content-Type'].startswith('text/html'):
                content = response.content
                try:
                    json_ = json.loads(content)
                    content = json.dumps(json_, sort_keys=True, indent=2)
                except ValueError:
                    pass
                response = HttpResponse('<html><body><pre>{}'
                                        '</pre></body></html>'.format(content))

        return response


# Middleware classes for debug toolbar.
middleware = ('debug_toolbar.middleware.DebugToolbarMiddleware',
              'server.debug.NonHtmlDebugToolbarMiddleware')
