"""Middleware for graceful database failure handling.

If the production PostgreSQL pool is temporarily exhausted
(``too many connections``), return a friendly 503 page instead of a raw
500 Internal Server Error so the site degrades gracefully.
"""

from django.db import OperationalError
from django.shortcuts import render
from django.http import HttpResponse


class DatabaseUnavailableMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except OperationalError:
            # Database is temporarily overloaded or unreachable.
            # Return 503 with a friendly retry message.
            return render(
                request,
                '503.html',
                status=503,
            )
