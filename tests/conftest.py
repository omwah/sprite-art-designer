from pathlib import Path

import pytest

from sprite_art import PaletteCatalog, Sprite, load_palette_catalog, load_sprite_directory

ASSETS = Path(__file__).parents[1] / "assets"


@pytest.fixture(scope="module")
def palettes() -> PaletteCatalog:
    return load_palette_catalog(ASSETS / "palettes.yaml")


@pytest.fixture(scope="module")
def sprites() -> dict[str, Sprite]:
    return load_sprite_directory(ASSETS / "sprites")
