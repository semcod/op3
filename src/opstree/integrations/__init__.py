"""Helpers that downstream projects (doql, redeploy) use to embed op3.

The most common pattern is:

    from opstree.integrations import make_compat_helpers

    _h = make_compat_helpers(
        env_var="REDEPLOY_USE_OP3",
        default_layers=("physical.display", "os.kernel", "os.config"),
        install_hint="pip install 'redeploy[op3]'",
    )
    op3_available = _h.op3_available
    op3_enabled   = _h.op3_enabled
    should_use_op3 = _h.should_use_op3
    require_op3   = _h.require_op3
    make_ssh_context = _h.make_ssh_context
    make_mock_context = _h.make_mock_context
    make_scanner = _h.make_scanner

This replaces ~50 lines of duplicated code per project.
"""

from .compat import CompatHelpers, make_compat_helpers

__all__ = ["CompatHelpers", "make_compat_helpers"]
