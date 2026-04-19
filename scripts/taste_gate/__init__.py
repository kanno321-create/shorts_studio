"""Taste Gate feedback pipeline — D-12 appender to .claude/failures/FAILURES.md.

Phase 9 ships record_feedback.py; Phase 10 may add taste_gate/selector.py for
auto selection of top-3/bottom-3 by 3-sec retention (currently manual).

Mirrors scripts/failures/__init__.py namespace discipline (stdlib-only downstream).
"""
