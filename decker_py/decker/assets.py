from __future__ import annotations

from pathlib import Path

import pygame


class AssetStore:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root
        packaged_root = Path(__file__).resolve().parent / "bundled"
        asset_root = repository_root if (repository_root / "DefaultGraphics").exists() else packaged_root
        self.graphics = asset_root / "DefaultGraphics"
        self.sounds = asset_root / "Sound"
        self.resources = asset_root / "RES"
        self._lookup: dict[str, Path] = {}
        self._images: dict[tuple[str, tuple[int, int] | None], pygame.Surface] = {}
        for directory in (self.graphics, self.sounds, self.resources):
            if directory.exists():
                self._lookup.update({path.name.lower(): path for path in directory.iterdir() if path.is_file()})
        self.mixer_ready = False
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                self.mixer_ready = True
            except pygame.error:
                self.mixer_ready = False
        else:
            self.mixer_ready = True

    def path(self, name: str) -> Path:
        try:
            return self._lookup[name.lower()]
        except KeyError as error:
            raise FileNotFoundError(f"Missing bundled asset: {name}") from error

    def image(self, name: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        key = (name.lower(), size)
        if key not in self._images:
            image = pygame.image.load(str(self.path(name))).convert_alpha()
            if size and image.get_size() != size:
                image = pygame.transform.smoothscale(image, size)
            self._images[key] = image
        return self._images[key]

    def sprite(self, sheet_name: str, index: int, cell_size: tuple[int, int]) -> pygame.Surface:
        sheet = self.image(sheet_name)
        columns = max(1, sheet.get_width() // cell_size[0])
        column = index % columns
        row = index // columns
        surface = pygame.Surface(cell_size, pygame.SRCALPHA).convert_alpha()
        source = pygame.Rect(column * cell_size[0], row * cell_size[1], *cell_size)
        surface.blit(sheet, (0, 0), source)
        return surface

    def play(self, name: str) -> None:
        if not self.mixer_ready:
            return
        try:
            pygame.mixer.Sound(str(self.path(name))).play()
        except (FileNotFoundError, pygame.error):
            pass

    def close(self) -> None:
        if self.mixer_ready:
            pygame.mixer.quit()
        self._images.clear()
