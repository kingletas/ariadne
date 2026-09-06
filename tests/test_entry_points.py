"""The ways somebody actually starts this, checked by reading the source.

The front end imports GTK at module level, so a suite that must run on a
machine without a toolkit cannot call these. It can still read them, and what
went wrong here was a signature and a call site disagreeing — which is exactly
what reading them catches.

This exists because `ariadne --app` from an applications menu died with a
TypeError while every test passed: the smoke run built the application object
directly and never went through `run()`.
"""

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "ariadne"


def function(path: Path, name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None
    )
    assert found is not None, f"{path.name} has no {name}()"
    return found


def required_arguments(fn: ast.FunctionDef) -> list[str]:
    positional = fn.args.posonlyargs + fn.args.args
    without_default = len(positional) - len(fn.args.defaults)
    return [a.arg for a in positional[:without_default]]


def test_the_window_opens_with_no_arguments():
    """An applications menu passes nothing at all."""
    run = function(PACKAGE / "app" / "main.py", "run")
    assert not required_arguments(run), (
        f"run() still requires {required_arguments(run)}, so launching from a "
        "menu raises before anything is drawn"
    )


def test_the_command_line_calls_it_that_way():
    """And the call site has to agree, which is the half that drifted."""
    source = (PACKAGE / "cli" / "main.py").read_text(encoding="utf-8")
    calls = [
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "run_app"
    ]
    assert calls, "the command line never reaches the window"
    assert any(not c.args and not c.keywords for c in calls), (
        "no call to run_app() passes nothing, so `--app` with no book cannot work"
    )


def test_every_front_end_entry_point_is_callable_bare():
    """Anything a desktop file or a menu can invoke takes no argument."""
    for module, name in (("app/main.py", "run"), ("app/main.py", "load_styles")):
        fn = function(PACKAGE / module, name)
        assert not required_arguments(fn), f"{module}:{name}() requires arguments"
