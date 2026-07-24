from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest

from sprite_art_designer.app import EdgeArtDesigner, _new_sprite
from sprite_art_designer.widgets import ArtCanvas

ROOT = Path(__file__).parents[1]


@pytest.mark.asyncio
async def test_app_mounts_wide_and_populates_editor() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        assert len(app.editor.sprites) == 12
        assert app.query_one("#nav-pane").display
        assert app.query_one("#canvas-pane").display
        assert app.query_one("#tools-pane").display
        assert app.query_one("#preview-pane").display
        assert app.query_one("#preview-matrix").render() is not None


@pytest.mark.asyncio
async def test_narrow_layout_uses_switchable_panels() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(80, 32)) as pilot:
        await pilot.pause()
        assert app._narrow
        assert app.query_one("#canvas-pane").display
        assert not app.query_one("#preview-pane").display
        await pilot.click("#panel-preview")
        await pilot.pause()
        assert app.query_one("#preview-pane").display
        assert not app.query_one("#workspace").display


def test_new_generic_sprite_uses_fixed_canvas_model() -> None:
    sprite = _new_sprite("test_icon", "Test Icon", "generic")
    assert sprite.kind == "generic"
    assert sprite.views["default"].axis == "fixed"
    assert sprite.views["default"].tiers[0].sections[0].variants[0].cells


@pytest.mark.asyncio
async def test_mouse_paint_marks_dirty_and_writes_recovery(
    tmp_path: Path,
) -> None:
    asset_root = tmp_path / "assets"
    copytree(ROOT / "assets", asset_root)
    app = EdgeArtDesigner(asset_root)
    async with app.run_test(size=(120, 42)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        original = canvas.variant.cells[0][0]
        canvas.set_glyph("◆" if original != "◆" else "█")
        content_offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=content_offset)
        await pilot.pause(0.6)
        assert app.editor.current_sprite_id in app.editor.dirty_sprites
        assert app.editor.recovery_path(app.editor.current_sprite_id).exists()
