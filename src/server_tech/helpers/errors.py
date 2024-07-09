from __future__ import annotations


class BaseServerTechError(Exception):
    """Base Server Technology Error."""


class NotSupportedServerTechError(BaseServerTechError):
    """Not supported by Server Technology."""


class RESTAPIServerTechError(BaseServerTechError):
    """Server Technology REST API base error."""
