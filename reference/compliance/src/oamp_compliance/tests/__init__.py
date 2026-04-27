"""Compliance test modules.

Importing these modules triggers the @registry.register decorators,
populating the global test registry with all MUST, SHOULD, and FUNC tests.
"""

from . import must
from . import should
from . import functional

__all__ = ["must", "should", "functional"]
