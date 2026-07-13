from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_diagnostics() -> dict:
    report = {"checks": [], "warnings": [], "errors": []}

    def check(name: str, ok: bool, detail: str = ""):
        report["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            report["errors"].append(f"{name}: {detail}")

    try:
        from app.config.loader import load_and_validate
        cfg, errors = load_and_validate()
        check("config_valid", not errors, "; ".join(errors) if errors else "config OK")
    except Exception as e:
        check("config_load", False, str(e))

    try:
        from app.tools.registry import tool_registry
        schemas = tool_registry.to_openai_schemas()
        check("tool_registry", len(schemas) > 0, f"{len(schemas)} tools registered")
    except Exception as e:
        check("tool_registry", False, str(e))

    try:
        from app.llm.router import llm_router
        providers = llm_router.list_providers()
        check("llm_providers", len(providers) > 0, f"providers: {', '.join(providers) if providers else 'none'}")
    except Exception as e:
        check("llm_providers", False, str(e))

    try:
        from app.graph.engine import GraphEngine
        check("graph_engine", True, "graph engine available")
    except Exception as e:
        check("graph_engine", False, str(e))

    try:
        from app.memory.manager import memory_manager
        check("memory_manager", True, "memory manager available")
    except Exception as e:
        check("memory_manager", False, str(e))

    try:
        import playwright
        check("playwright", True, "playwright available")
    except ImportError:
        check("playwright", False, "playwright not installed")

    report["healthy"] = len(report["errors"]) == 0
    return report


def doctor_cli():
    report = run_diagnostics()
    print("AIOS Diagnostics")
    print("=" * 40)
    for c in report["checks"]:
        status = "PASS" if c["ok"] else "FAIL"
        print(f"[{status}] {c['name']}: {c['detail']}")
    print("=" * 40)
    if report["healthy"]:
        print("All systems operational.")
    else:
        print(f"{len(report['errors'])} error(s) found.")
