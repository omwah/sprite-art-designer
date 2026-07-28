from __future__ import annotations

from io import StringIO
from pathlib import Path
from shutil import copy

import pytest
from rich.console import Console

from sprite_art_designer import render_ships

ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"


def _console_output() -> tuple[Console, StringIO]:
    stream = StringIO()
    return Console(file=stream, color_system=None, width=120), stream


def test_default_console_forces_truecolor_output() -> None:
    console = render_ships._default_console()

    assert console.is_terminal
    assert console.color_system == "truecolor"


def test_cli_renders_selected_ship_and_tier_with_explicit_seed() -> None:
    console, stream = _console_output()

    result = render_ships.main(
        [
            "--ship-type",
            "fighter",
            "--tier",
            "compact",
            "--archetype",
            "ribbon_salvager",
            "--seed",
            "17",
        ],
        console=console,
    )

    output = stream.getvalue()
    assert result == 0
    assert "archetype=ribbon_salvager · seed=17" in output
    assert "Fighter (fighter) · Horizontal" in output
    assert "Compact (compact)" in output
    assert "Full Detail (full)" not in output
    assert "Transport (transport)" not in output


def test_cli_defaults_to_every_tier_for_a_selected_ship() -> None:
    console, stream = _console_output()

    render_ships.main(["--ship-type", "fighter", "--seed", "3"], console=console)

    output = stream.getvalue()
    assert "Full Detail (full)" in output
    assert "Medium (medium)" in output
    assert "Compact (compact)" in output


def test_cli_uses_random_seed_when_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    console, stream = _console_output()
    monkeypatch.setattr(render_ships.secrets, "randbits", lambda bits: 4242)

    render_ships.main(
        ["--ship-type", "fighter", "--tier", "compact"],
        console=console,
    )

    assert "seed=4242" in stream.getvalue()


def test_cli_loads_a_custom_sprite_directory(tmp_path: Path) -> None:
    copy(ASSETS / "sprites" / "ships" / "warship.yaml", tmp_path / "warship.yaml")
    console, stream = _console_output()

    render_ships.main(
        [str(tmp_path), "--tier", "compact", "--seed", "9"],
        console=console,
    )

    output = stream.getvalue()
    assert f"Sprites: {tmp_path.resolve()}" in output
    assert "Warship (warship)" in output
    assert "Fighter (fighter)" not in output


def test_cli_rejects_unknown_ship_type(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="2"):
        render_ships.main(["--ship-type", "missing"])

    assert "unknown ship type(s): missing" in capsys.readouterr().err
