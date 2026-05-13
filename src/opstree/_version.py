"""Version information — single source of truth for op3 package version.

Kept in sync with the top-level ``VERSION`` file and ``pyproject.toml``
by release tooling. All runtime code importing a version string MUST
import ``__version__`` from this module (or from ``opstree``) rather
than hardcoding a literal.
"""

__version__ = "0.2.0"
