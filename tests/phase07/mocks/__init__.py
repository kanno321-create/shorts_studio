"""Phase 7 deterministic adapter mocks package (Wave 1 per 07-02-PLAN.md).

Each module here shadows a real adapter under scripts/orchestrator/api/ with
a deterministic, production-safe mock. All mocks default
``allow_fault_injection=False`` per CONTEXT D-3 so accidental production
wiring fails safe (no injected failures reach prod).
"""
