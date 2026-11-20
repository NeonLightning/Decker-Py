import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from decker.ui import DeckerApp


def test_app_opens_and_renders_original_screens() -> None:
    root = Path(__file__).resolve().parents[2]
    app = DeckerApp(root)
    try:
        app._render()
        assert app.scene == "intro"
        app.show_new_game()
        app.text_input = "Smoke Test"
        app._create_character()
        app._render()
        assert app.scene == "home"
        assert app.character is not None
        app.character.accept_contract(0)
        app.enter_matrix()
        app._render()
        assert app.scene == "matrix"
        assert app.character.matrix is not None
        assert app.buttons
        assert any(button.tooltip for button in app.buttons)
        tooltip = next((button for button in app.buttons if button.tooltip), None)
        assert tooltip is not None
        app.hover = tooltip.rect.center
        app._render()
        matrix_bitmap_buttons = [button for button in app.buttons if button.rect.width == 24]
        assert matrix_bitmap_buttons
        assert all(button.image is not None for button in matrix_bitmap_buttons)
        app.open_dialog("deck", "CYBERDECK")
        app._render()
        assert any(button.tooltip for button in app.buttons)
    finally:
        app.assets.close()
        import pygame
        pygame.quit()
