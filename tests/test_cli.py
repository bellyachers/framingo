from pathlib import Path

from framingo.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _check(name, capsys):
    code = main(
        ["check", str(EXAMPLES / name), "--context", str(EXAMPLES / "context.fr"), "--core", str(EXAMPLES / "core.fr")]
    )
    return code, capsys.readouterr().out


def test_grounded_example_exits_zero(capsys):
    code, out = _check("grounded.fr", capsys)
    assert code == 0 and "derived" in out


def test_hallucinated_example_exits_nonzero(capsys):
    code, out = _check("hallucinated.fr", capsys)
    assert code == 1 and "ungrounded word `Mary`" in out


def test_parse_prints_canonical_form(capsys):
    assert main(["parse", str(EXAMPLES / "core.fr")]) == 0
    assert capsys.readouterr().out.startswith("RULE: Action: Drop")
