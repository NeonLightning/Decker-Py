from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys
from typing import Callable

import pygame

from .assets import AssetStore
from .model import (
    Character, HARDWARE_NAMES, CHIP_NAMES, LIFESTYLES, LIFESTYLE_COST, MONTH_NAMES,
    MAX_HEALTH, NODE_TYPE_NAMES, PROGRAM_NAMES, PROGRAM_COMPLEXITY, CONTRACT_TYPES, Contract, Ice, Program, SourceCode,
)
from .storage import default_save_directory, load_game, quick_save_path, save_game

SCREEN_SIZE = (640, 480)
BLACK = (4, 7, 10)
PANEL = (15, 29, 36)
PANEL_LIGHT = (24, 48, 57)
BORDER = (65, 142, 151)
TEXT = (211, 234, 229)
DIM = (125, 157, 155)
CYAN = (80, 221, 217)
GREEN = (70, 214, 118)
YELLOW = (236, 201, 83)
RED = (233, 86, 83)
WHITE = (240, 244, 239)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: Callable[[], None]
    enabled: bool = True
    image: pygame.Surface | None = None
    hover_image: pygame.Surface | None = None
    tooltip: str = ""


class UserMessage(Exception):
    pass


class DeckerApp:
    def __init__(self, repository_root: Path) -> None:
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption("Decker - A Cyberspace RPG")
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.root = repository_root
        self.assets = AssetStore(repository_root)
        self.font_tiny = pygame.font.Font(None, 15)
        self.font = pygame.font.Font(None, 20)
        self.font_big = pygame.font.Font(None, 30)
        self.font_title = pygame.font.Font(None, 40)
        self.font_mono = pygame.font.Font(pygame.font.match_font("monospace"), 14)
        self.character: Character | None = None
        self.running = True
        self.scene = "intro"
        self.dialog: str | None = None
        self.dialog_title = ""
        self.dialog_text: list[str] = []
        self.selection = 0
        self.selected_contract: int | None = None
        self.selected_source = 0
        self.project_type = "software"
        self.project_class = 0
        self.project_rating = 1
        self.build_name = ""
        self.build_load = True
        self.build_trash = True
        self.build_unload = False
        self.scroll = 0
        self.text_input = ""
        self.input_cursor_visible = True
        self.hover = (-1, -1)
        self.buttons: list[Button] = []
        self.hotspots: list[Button] = []
        self.messages: list[str] = []
        self.selected_program = 0
        self.selected_ice = 0
        self.pending_action: Callable[[str], None] | None = None
        self.bonus = "none"
        self._load_status = ""
        self.map_zoom = False
        self.new_image = 0
        self.new_ironman = False
        self.new_tooltips = False
        self.file_action = "download"
    def run(self) -> int:
        try:
            while self.running:
                self.clock.tick(60)
                self._process_events()
                self._render()
                pygame.display.flip()
        finally:
            self.assets.close()
            pygame.quit()
        return 0

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                self.hover = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._click(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                maximum = 0
                if self.dialog == "shop" and self.character:
                    maximum = max(0, len(self.character.shop) - 9)
                elif self.dialog == "deck" and self.character:
                    maximum = max(0, len(self.character.programs) - 9)
                self.scroll = max(0, min(maximum, self.scroll + (-1 if event.button == 4 else 1)))
            elif event.type == pygame.KEYDOWN:
                self._key(event)

    def _key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            if self.dialog:
                self.close_dialog()
            elif self.scene == "matrix":
                self.disconnect()
            elif self.scene == "home":
                self.scene = "intro"
            return
        if self.dialog == "new":
            if event.key == pygame.K_RETURN and self.text_input.strip():
                self._create_character()
            elif event.key == pygame.K_BACKSPACE:
                self.text_input = self.text_input[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.text_input) < 32:
                self.text_input += event.unicode
            return
        if self.dialog == "rest":
            if event.key == pygame.K_RETURN:
                self._rest_selected_days()
            return
        if self.dialog == "build_project":
            if event.key == pygame.K_RETURN and self.build_name.strip():
                self.build_source()
            elif event.key == pygame.K_BACKSPACE:
                self.build_name = self.build_name[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.build_name) < 32:
                self.build_name += event.unicode
            return
        if event.key in (pygame.K_F5, pygame.K_s) and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.save()
        elif event.key in (pygame.K_F9, pygame.K_l) and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.quick_load()
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selection += 1
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selection -= 1
        elif event.key == pygame.K_RETURN and self.dialog:
            self._enter_dialog_selection()
        elif self.scene == "matrix":
            directions = {pygame.K_w: "N", pygame.K_d: "E", pygame.K_s: "S", pygame.K_a: "W"}
            if event.key in directions and self.character and self.character.matrix:
                self.character.matrix.move(directions[event.key])
                self.assets.play("Move.wav")

    def _click(self, position: tuple[int, int]) -> None:
        if self.dialog == "message":
            self.close_dialog()
            return
        for hotspot in reversed(self.hotspots):
            if hotspot.rect.collidepoint(position) and hotspot.enabled:
                hotspot.action()
                return
        for button in reversed(self.buttons):
            if button.rect.collidepoint(position) and button.enabled:
                button.action()
                self.assets.play("Click.wav") if self._asset_exists("Click.wav") else None
                return
        if self.scene == "intro":
            panel = pygame.Rect(120, 55, 400, 370)
            if panel.collidepoint(position):
                pass

    def _asset_exists(self, name: str) -> bool:
        try:
            self.assets.path(name)
            return True
        except FileNotFoundError:
            return False

    def _render(self) -> None:
        self.buttons.clear()
        self.hotspots.clear()
        self.screen.fill(BLACK)
        if self.scene == "intro":
            self._draw_intro()
        elif self.scene == "home":
            self._draw_home()
        elif self.scene == "matrix":
            self._draw_matrix()
        if self.dialog:
            self._draw_dialog()
        self._draw_tooltip()

    def _draw_intro(self) -> None:
        for index in range(14):
            color = (11, 24 + index, 31 + index * 2)
            pygame.draw.rect(self.screen, color, pygame.Rect(0, index * 35, SCREEN_SIZE[0], 36))
        panel = pygame.Rect(132, 52, 376, 376)
        self._panel(panel, "DECKER")
        self._text("A CYBERSPACE RPG", panel.left + 18, panel.top + 48, self.font_big, WHITE)
        pygame.draw.line(self.screen, BORDER, (panel.left + 18, panel.top + 78), (panel.right - 18, panel.top + 78), 1)
        self._wrapped(
            "Accept contracts. Build your cyberdeck. Enter hostile systems. Defeat ICE and complete the job before the trace closes in.",
            pygame.Rect(panel.left + 18, panel.top + 98, panel.width - 36, 82), self.font, TEXT,
        )
        self._button(Button(pygame.Rect(panel.left + 70, panel.top + 204, panel.width - 140, 36), "NEW GAME", self.show_new_game))
        self._button(Button(pygame.Rect(panel.left + 70, panel.top + 248, panel.width - 140, 36), "LOAD GAME", self.show_load))
        self._button(Button(pygame.Rect(panel.left + 70, panel.top + 292, panel.width - 140, 36), "QUIT", self.quit))
        self._text("Linux Python Edition · GPLv2+", panel.left + 18, panel.bottom - 25, self.font_tiny, DIM)

    def _draw_home(self) -> None:
        assert self.character
        self.screen.fill(BLACK)
        x0 = (SCREEN_SIZE[0] - 214) // 2
        y0 = (SCREEN_SIZE[1] - 232) // 2
        try:
            self.screen.blit(self.assets.image("HOME_MAIN.bmp", (214, 232)), (x0, y0))
        except FileNotFoundError:
            self._panel(pygame.Rect(x0, y0, 214, 232), "HOME")
        specs = (
            ("Char", "HOME_Char0.bmp", self.show_character),
            ("Deck", "HOME_Deck0.bmp", self.show_deck),
            ("Contracts", "HOME_Contract0.bmp", self.show_contracts),
            ("Shop", "HOME_Shop0.bmp", self.show_shop),
            ("Projects", "HOME_Project0.bmp", self.show_projects),
            ("Rest", "HOME_Rest0.bmp", self.show_rest),
            ("Matrix", "HOME_Matrix0.bmp", self.enter_matrix),
            ("Options", "Home_Options0.bmp", self.show_options),
        )
        for index, (label, image, action) in enumerate(specs):
            rect = pygame.Rect(x0 + 9, y0 + 9 + index * 27, 24, 24)
            try:
                bitmap = self.assets.image(image, (24, 24))
                hover = self.assets.image(image.replace("0.bmp", "1.bmp"), (24, 24))
            except FileNotFoundError:
                bitmap = hover = None
            self._button(Button(rect, "", action, image=bitmap, hover_image=hover, tooltip=label))

    def _draw_matrix(self) -> None:
        assert self.character and self.character.matrix
        run = self.character.matrix
        try:
            self.screen.blit(self.assets.image("MATRIX_Main.bmp", SCREEN_SIZE), (0, 0))
        except FileNotFoundError:
            self.screen.fill(PANEL)
        self._draw_node_view(pygame.Rect(194, 49, 240, 240))
        self._draw_matrix_map(pygame.Rect(451, 12, 177, 166))
        self._draw_program_list(pygame.Rect(10, 42, 169, 397))
        self._draw_messages(pygame.Rect(194, 367, 434, 101))
        self._draw_matrix_status()
        self._draw_matrix_buttons()
        node = run.node
        pygame.draw.rect(self.screen, (21, 22, 75), pygame.Rect(194, 296, 96, 16))
        self._text(node.name[:16], 198, 297, self.font_tiny, WHITE)
        local_ice = run.local_ice
        if local_ice:
            self.selected_ice %= len(local_ice)
            ice = local_ice[self.selected_ice]
            pygame.draw.rect(self.screen, (21, 22, 75), pygame.Rect(338, 296, 96, 16))
            self._text(ice.name[:16], 342, 297, self.font_tiny, WHITE)
            try:
                icon = self.assets.sprite("il_ice.bmp", ice.ice_type * 2 + int(ice.hostile), (24, 24))
                icon.set_colorkey(icon.get_at((0, 0)))
                pygame.draw.rect(self.screen, RED if ice.hostile else GREEN, pygame.Rect(307, 296, 24, 24))
                self.screen.blit(icon, (307, 296))
            except FileNotFoundError:
                pass
            self._bar(354, 342, ice.health, 4 + ice.rating * 3, RED)
        self._draw_active_programs()
        self._bar(548, 195, run.deck_health, MAX_HEALTH, RED)
        if self.character.hardware[4]:
            self._bar(548, 220, run.mental_health, MAX_HEALTH, CYAN)
            self._bar(548, 234, self.character.physical_health, MAX_HEALTH, GREEN)
        else:
            try:
                self.screen.blit(self.assets.image("MATRIX_Bio_Cover.bmp", (110, 36)), (525, 213))
            except FileNotFoundError:
                pass
        if self.character.hardware[3]:
            self._bar(548, 309, run.trace_turns, 15, YELLOW)
        else:
            try:
                self.screen.blit(self.assets.image("MATRIX_Trace_Cover.bmp", (110, 22)), (525, 302))
            except FileNotFoundError:
                pass
        shield = next((p.rating for p in self.character.programs if p.loaded and p.class_id == 8), 0)
        self._bar(548, 259, shield, max(1, shield), CYAN)
        pygame.draw.rect(self.screen, (16, 16, 45), pygame.Rect(206, 342, 84, 8))
        if run.alert:
            pygame.draw.rect(self.screen, YELLOW if run.alert == 1 else RED,
                             pygame.Rect(206, 342, 28 * min(3, run.alert), 8))

    def _draw_node_view(self, area: pygame.Rect) -> None:
        assert self.character and self.character.matrix
        run = self.character.matrix
        node_files = ("NODE_CPU.BMP", "NODE_SPU.BMP", "NODE_COP.BMP", "NODE_DS.BMP", "NODE_IO.BMP", "NODE_JUN.BMP", "node_portal.bmp", "node_portal.bmp")
        try:
            self.screen.blit(self.assets.image(node_files[run.node.node_type], area.size), area)
        except FileNotFoundError:
            pygame.draw.rect(self.screen, BLACK, area)
        line_specs = (
            ("N", "line_ns.bmp", (107, 0)), ("E", "line_ew.bmp", (227, 107)),
            ("S", "line_ns.bmp", (107, 227)), ("W", "line_ew.bmp", (0, 107)),
        )
        for direction, filename, offset in line_specs:
            if direction in run.node.neighbors:
                try:
                    self.screen.blit(self.assets.image(filename), (area.left + offset[0], area.top + offset[1]))
                except FileNotFoundError:
                    pass
        try:
            character = self.assets.sprite("MISC_Characters.bmp", self.character.image, (24, 24))
            character.set_colorkey(character.get_at((0, 0)))
            self.screen.blit(character, (area.left + 108, area.top + 108))
        except FileNotFoundError:
            pygame.draw.circle(self.screen, CYAN, (area.left + 120, area.top + 120), 8)
        for offset, ice in enumerate(run.local_ice[:8]):
            ice_index = ice.ice_type * 2 + (1 if ice.hostile else 0)
            x = area.left + 12 + ice.grid_x * 24
            y = area.top + 12 + ice.grid_y * 24
            try:
                sprite = self.assets.sprite("il_ice.bmp", ice_index, (24, 24))
                sprite.set_colorkey(sprite.get_at((0, 0)))
                self.screen.blit(sprite, (x, y))
            except FileNotFoundError:
                pygame.draw.rect(self.screen, RED, pygame.Rect(x + 4, y + 4, 16, 16), 2)
            target_rect = pygame.Rect(x - 3, y - 3, 30, 30)
            self.hotspots.append(Button(target_rect, "", lambda i=offset: self.select_ice(i), tooltip=ice.name))
            if offset == self.selected_ice % max(1, len(run.local_ice)):
                try:
                    marker = self.assets.sprite("il_misc.bmp", 0, (24, 24))
                    marker.set_colorkey(marker.get_at((0, 0)))
                    self.screen.blit(marker, (x, y))
                except FileNotFoundError:
                    pygame.draw.rect(self.screen, WHITE, target_rect, 1)

    def _draw_active_programs(self) -> None:
        assert self.character and self.character.matrix
        run = self.character.matrix
        active_character = [program for program in self.character.programs
                            if program.loaded and program.class_id in {8, 12, 13, 20}]
        for offset, program in enumerate(active_character[:5]):
            try:
                icon = self.assets.sprite("software_il.bmp", program.class_id, (16, 16))
                self.screen.blit(icon, (532 + offset * 18, 334))
            except FileNotFoundError:
                pygame.draw.rect(self.screen, GREEN, pygame.Rect(532 + offset * 18, 334, 16, 16), 1)
        node_states = ((5, run.node.silence), (9, run.node.smoke),
                       (17, False), (25, run.contract_type == 9 and run.complete()))
        for offset, (class_id, active) in enumerate(node_states):
            if active:
                try:
                    self.screen.blit(self.assets.sprite("software_il.bmp", class_id, (16, 16)),
                                     (194 + offset * 18, 319))
                except FileNotFoundError:
                    pygame.draw.rect(self.screen, GREEN, pygame.Rect(194 + offset * 18, 319, 16, 16), 1)
        if run.local_ice:
            target = run.local_ice[self.selected_ice % len(run.local_ice)]
            states = ((target.slow_turns, 3), (target.confuse_turns, 6), (target.weaken_turns, 7), (int(target.analyzed), 16))
            for offset, (active, class_id) in enumerate(states):
                if active:
                    try:
                        self.screen.blit(self.assets.sprite("software_il.bmp", class_id, (16, 16)), (338 + offset * 18, 319))
                    except FileNotFoundError:
                        pygame.draw.rect(self.screen, YELLOW, pygame.Rect(338 + offset * 18, 319, 16, 16), 1)

    def _draw_matrix_map(self, area: pygame.Rect) -> None:
        assert self.character and self.character.matrix
        pygame.draw.rect(self.screen, (0, 0, 0), area)
        run = self.character.matrix
        points: dict[int, tuple[int, int]] = {}
        grid = 30 if self.map_zoom else 18
        origin_x = max(area.left + 8, area.centerx - (run.node.x - 1) * grid - 8)
        origin_y = max(area.top + 8, area.centery - (run.node.y - 1) * grid - 8)
        for index, node in enumerate(run.nodes):
            if not node.mapped and index != run.current_node:
                continue
            point = (origin_x + (node.x - 1) * grid, origin_y + (node.y - 1) * grid)
            if area.collidepoint(point):
                points[index] = point
        for index, node in enumerate(run.nodes):
            if index not in points:
                continue
            for direction in ("E", "S"):
                neighbor = node.neighbors.get(direction)
                if neighbor in points:
                    start = (points[index][0] + 8, points[index][1] + 8)
                    end = (points[neighbor][0] + 8, points[neighbor][1] + 8)
                    pygame.draw.line(self.screen, (0, 78, 125), start, end, 4)
                    pygame.draw.line(self.screen, (0, 151, 174), start, end, 2)
        for index, point in points.items():
            node = run.nodes[index]
            try:
                icon = self.assets.sprite("Node_IL_16.bmp", node.node_type, (16, 16))
                self.screen.blit(icon, point)
            except FileNotFoundError:
                pygame.draw.rect(self.screen, CYAN, pygame.Rect(point, (16, 16)), 1)
            if index == run.current_node:
                pygame.draw.circle(self.screen, WHITE, (point[0] + 8, point[1] + 8), 11, 1)

    def _draw_program_list(self, area: pygame.Rect) -> None:
        assert self.character
        pygame.draw.rect(self.screen, (0, 5, 8), area)
        loaded = [(index, program) for index, program in enumerate(self.character.programs) if program.loaded]
        widths = (20, 96, 42)
        self._table_row(area.left + 2, area.top + 2, widths, ("", "Program", "Rating"), color=CYAN)
        for row, (index, program) in enumerate(loaded[:16]):
            rect = self._table_row(
                area.left + 2, area.top + 28 + row * 21, widths,
                ("", program.name, str(program.rating)), selected=index == self.selected_program,
                color=WHITE,
            )
            try:
                highlighted = ((program.load_default and program.class_id in (0, 1, 2)) or
                               program.class_id in {8, 12, 13, 20})
                icon_index = program.class_id + (26 if highlighted else 0)
                self.screen.blit(self.assets.sprite("software_il.bmp", icon_index, (16, 16)),
                                 (rect.left + 2, rect.top + 3))
            except FileNotFoundError:
                pass
            self._button(Button(rect, "", lambda i=index: self.select_program(i), tooltip=program.name), transparent=True)

    def _draw_messages(self, area: pygame.Rect) -> None:
        assert self.character and self.character.matrix
        pygame.draw.rect(self.screen, (2, 8, 10), area)
        lines = self.character.matrix.messages[-5:]
        for index, line in enumerate(lines):
            self._text(line[:74], area.left + 5, area.top + 5 + index * 18, self.font_tiny, TEXT)

    def _draw_matrix_status(self) -> None:
        assert self.character and self.character.matrix
        run = self.character.matrix
        minutes, seconds = divmod(run.turns, 60)
        self._text(f"{minutes:02d}:{seconds:02d}", 138, 12, self.font_tiny, WHITE)

    def _draw_matrix_buttons(self) -> None:
        assert self.character and self.character.matrix
        run = self.character.matrix
        local_ice = run.local_ice
        selected = self.selected_program_object()
        has_program = lambda class_id: any(p.loaded and p.class_id == class_id for p in self.character.programs)
        default_attack = next((p for p in self.character.programs if p.loaded and p.load_default and p.class_id in (0, 1, 2)), None)
        specs = (
            ("MATRIX_Attack0.bmp", (439, 193), self.matrix_attack, bool(local_ice and default_attack)),
            ("MATRIX_Arrow_n0.bmp", (466, 193), lambda: self.move("N"), "N" in run.node.neighbors),
            ("MATRIX_Deceive0.bmp", (493, 193), self.matrix_deceive, bool(local_ice and has_program(14))),
            ("MATRIX_Arrow_w0.bmp", (439, 220), lambda: self.move("W"), "W" in run.node.neighbors),
            ("MATRIX_Wait0.bmp", (466, 220), self.wait_turn, True),
            ("MATRIX_Arrow_e0.bmp", (493, 220), lambda: self.move("E"), "E" in run.node.neighbors),
            ("MATRIX_View_Ice0.bmp", (439, 247), self.show_ice, bool(local_ice and has_program(16))),
            ("MATRIX_Arrow_s0.bmp", (466, 247), lambda: self.move("S"), "S" in run.node.neighbors),
            ("MATRIX_scan0.bmp", (493, 247), self.matrix_scan, run.node.node_type in (3, 4) and has_program(17)),
            ("MATRIX_Char0.bmp", (439, 274), self.show_character, True),
            ("MATRIX_Deck0.bmp", (466, 274), self.show_deck, True),
            ("MATRIX_Contract0.bmp", (493, 274), self.show_current_contract, True),
            ("MATRIX_Disconnect0.bmp", (466, 328), self.disconnect, True),
            ("MATRIX_Options0.bmp", (493, 328), self.show_options, True),
            ("MATRIX_Run_Program0.bmp", (10, 446), self.run_selected_program, bool(selected and selected.loaded)),
            ("MATRIX_Set_Def0.bmp", (37, 446), self.set_program_default, bool(selected and selected.class_id in (0, 1, 2))),
            ("MATRIX_Load0.bmp", (64, 446), self.show_deck, True),
            ("MATRIX_Unload0.bmp", (91, 446), self.unload_program, bool(selected and selected.loaded)),
        )
        for filename, position, action, enabled in specs:
            self._icon_button(filename, position, action, enabled)
        try:
            zoom_rect = pygame.Rect(431, 10, 15, 24)
            zoom_image = self.assets.image("MATRIX_Map_Zoom0.bmp", zoom_rect.size)
            zoom_hover = self.assets.image("MATRIX_Map_Zoom1.bmp", zoom_rect.size)
            self._button(Button(zoom_rect, "", self.toggle_map_zoom, image=zoom_image,
                                hover_image=zoom_hover, tooltip="Zoom map"))
        except FileNotFoundError:
            self._button(Button(pygame.Rect(431, 10, 15, 24), "Z", self.toggle_map_zoom, tooltip="Zoom map"))
        self._node_action_buttons()

    def toggle_map_zoom(self) -> None:
        self.map_zoom = not self.map_zoom

    def _node_action_buttons(self) -> None:
        assert self.character and self.character.matrix
        node_type = self.character.matrix.node.node_type
        actions: list[tuple[str, tuple[int, int], Callable[[], None]]] = []
        if node_type == 3:
            actions = [
                ("MATRIX_Getfile0.bmp", (439, 301), lambda: self.node_action("download")),
                ("MATRIX_Edit0.bmp", (466, 301), lambda: self.node_action("edit")),
                ("MATRIX_Erase0.bmp", (493, 301), lambda: self.node_action("erase")),
            ]
        elif node_type == 0:
            actions = [
                ("MATRIX_Getmap0.bmp", (439, 301), lambda: self.node_action("map")),
                ("MATRIX_Crash0.bmp", (466, 301), lambda: self.node_action("crash")),
                ("MATRIX_Kill_Shutdown0.bmp", (493, 301), lambda: self.node_action("crash")),
                ("MATRIX_Backdoor0.bmp", (439, 328), lambda: self.node_action("backdoor")),
            ]
        elif node_type == 4:
            actions = [("MATRIX_Use_io0.bmp", (439, 301), lambda: self.node_action("io"))]
        elif node_type in (6, 7):
            actions = [("MATRIX_Enter_Portal0.bmp", (439, 301), lambda: self.node_action("portal"))]
        for filename, position, action in actions:
            self._icon_button(filename, position, action)

    def _icon_button(self, filename: str, position: tuple[int, int], action: Callable[[], None], enabled: bool = True) -> None:
        rect = pygame.Rect(position[0], position[1], 24, 24)
        tooltips = {
            "MATRIX_Attack": "Attack using the selected attack program",
            "MATRIX_Arrow_n": "Move north", "MATRIX_Arrow_e": "Move east",
            "MATRIX_Arrow_s": "Move south", "MATRIX_Arrow_w": "Move west",
            "MATRIX_Deceive": "Run the highest-rated Deceive program",
            "MATRIX_Wait": "Wait one turn", "MATRIX_View_Ice": "View targeted ICE",
            "MATRIX_scan": "Scan node", "MATRIX_Char": "View character statistics",
            "MATRIX_Deck": "View cyberdeck", "MATRIX_Contract": "View current contract",
            "MATRIX_Disconnect": "Disconnect from the Matrix", "MATRIX_Options": "Game options",
            "MATRIX_Run_Program": "Run selected program", "MATRIX_Set_Def": "Set default program",
            "MATRIX_Load": "Load selected program", "MATRIX_Unload": "Unload selected program",
            "MATRIX_Getfile": "Download a datastore file", "MATRIX_Edit": "Edit a datastore file",
            "MATRIX_Erase": "Erase a datastore file", "MATRIX_Getmap": "Get an area map",
            "MATRIX_Crash": "Crash the system", "MATRIX_Kill_Shutdown": "Cancel system shutdown",
            "MATRIX_Backdoor": "Create a backdoor", "MATRIX_Use_io": "Activate I/O",
            "MATRIX_Enter_Portal": "Enter portal", "MATRIX_Kill_Alarm": "Cancel an alert",
        }
        stem = filename[:-5]
        try:
            bitmap_name = filename if enabled else filename.replace("0.bmp", "2.bmp")
            bitmap = self.assets.image(bitmap_name, (24, 24))
            hover = self.assets.image(filename.replace("0.bmp", "1.bmp"), (24, 24)) if enabled else bitmap
        except FileNotFoundError:
            bitmap = hover = None
        self._button(Button(rect, filename.split("_")[-1], action, enabled, bitmap, hover, tooltips.get(stem, "")))

    def _button(self, button: Button, transparent: bool = False) -> None:
        self.buttons.append(button)
        if button.rect.width <= 0:
            return
        if transparent:
            return
        hovered = button.rect.collidepoint(self.hover)
        if button.image:
            self.screen.blit(button.hover_image if hovered and button.enabled and button.hover_image else button.image,
                             button.rect)
            return
        color = PANEL_LIGHT if not hovered else (35, 76, 84)
        if not button.enabled:
            color = (26, 32, 34)
        pygame.draw.rect(self.screen, color, button.rect)
        pygame.draw.rect(self.screen, BORDER if button.enabled else (58, 70, 70), button.rect, 1)
        if button.label:
            image = self.font.render(button.label, True, TEXT if button.enabled else DIM)
            self.screen.blit(image, image.get_rect(center=button.rect.center))

    def _draw_tooltip(self) -> None:
        if self.character is not None and self.character.tooltips is False:
            return
        hovered = next((item for item in reversed(self.buttons + self.hotspots)
                        if item.tooltip and item.rect.collidepoint(self.hover)), None)
        if hovered is None:
            return
        padding = 6
        max_text_width = 250
        words = hovered.tooltip.split()
        lines: list[str] = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and self.font_tiny.size(candidate)[0] > max_text_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        rendered = [self.font_tiny.render(value, True, (18, 20, 20)) for value in lines]
        width = min(SCREEN_SIZE[0] - 8, max((surface.get_width() for surface in rendered), default=0) + padding * 2)
        height = sum(surface.get_height() for surface in rendered) + padding * 2
        rect = pygame.Rect(self.hover[0] + 14, self.hover[1] + 18, width, height)
        rect.right = min(rect.right, SCREEN_SIZE[0] - 4)
        rect.bottom = min(rect.bottom, SCREEN_SIZE[1] - 4)
        rect.left = max(4, rect.left)
        rect.top = max(4, rect.top)
        pygame.draw.rect(self.screen, (245, 236, 184), rect)
        pygame.draw.rect(self.screen, (55, 48, 27), rect, 1)
        y = rect.top + padding
        for surface in rendered:
            self.screen.blit(surface, (rect.left + padding, y))
            y += surface.get_height()

    def _table_row(self, x: int, y: int, widths: tuple[int, ...], values: tuple[str, ...],
                   *, selected: bool = False, color: tuple[int, int, int] = TEXT,
                   font: pygame.font.Font | None = None) -> pygame.Rect:
        font = font or self.font_mono
        row = pygame.Rect(x, y, sum(widths), font.get_linesize() + 8)
        if selected:
            pygame.draw.rect(self.screen, PANEL_LIGHT, row)
        cursor = x + 5
        for index, (width, value) in enumerate(zip(widths, values)):
            available = max(1, width - 10)
            rendered = value
            while rendered and font.size(rendered + ("…" if rendered != value else ""))[0] > available:
                rendered = rendered[:-1]
            if rendered != value:
                rendered += "…"
            image = font.render(rendered, True, color)
            if index > 0 and index < len(widths) - 1:
                self.screen.blit(image, (cursor, y + 4))
            elif index == len(widths) - 1:
                self.screen.blit(image, (x + sum(widths[:index]) + width - 5 - image.get_width(), y + 4))
            else:
                self.screen.blit(image, (cursor, y + 4))
            cursor += width
        return row

    def _panel(self, rect: pygame.Rect, title: str) -> None:
        pygame.draw.rect(self.screen, (7, 17, 21), rect)
        pygame.draw.rect(self.screen, BORDER, rect, 2)
        pygame.draw.rect(self.screen, PANEL_LIGHT, pygame.Rect(rect.left, rect.top, rect.width, 34))
        self._text(title, rect.left + 12, rect.top + 8, self.font_big, CYAN)

    def _text(self, text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self.screen.blit(font.render(str(text), True, color), (x, y))

    def _wrapped(self, text: str, rect: pygame.Rect, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        words = text.split()
        lines: list[str] = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] > rect.width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        line_height = font.get_linesize()
        for index, item in enumerate(lines):
            if rect.top + index * line_height > rect.bottom - line_height:
                break
            self._text(item, rect.left, rect.top + index * line_height, font, color)

    def _bar(self, x: int, y: int, value: int, maximum: int, color: tuple[int, int, int]) -> None:
        width = 72
        pygame.draw.rect(self.screen, (12, 15, 15), pygame.Rect(x, y, width, 9))
        pygame.draw.rect(self.screen, color, pygame.Rect(x, y, int(width * max(0, min(maximum, value)) / maximum), 9))

    def open_dialog(self, kind: str, title: str, text: str | list[str] | None = None) -> None:
        self.dialog = kind
        self.dialog_title = title
        self.dialog_text = [text] if isinstance(text, str) else list(text or [])
        self.selection = 0
        if kind not in ("contract_details", "new_project", "build_project"):
            self.scroll = 0

    def close_dialog(self) -> None:
        self.dialog = None
        self.pending_action = None

    def show_message(self, title: str, text: str) -> None:
        self.open_dialog("message", title, text)

    def _draw_dialog(self) -> None:
        overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(74, 44, 492, 388)
        self._panel(rect, self.dialog_title)
        self._button(Button(pygame.Rect(rect.right - 32, rect.top + 4, 24, 24), "X", self.close_dialog))
        body = pygame.Rect(rect.left + 15, rect.top + 47, rect.width - 30, rect.height - 100)
        if self.dialog == "new":
            self._draw_new_dialog(body)
        elif self.dialog == "load":
            self._draw_load_dialog(body)
        elif self.dialog == "character":
            self._draw_character_dialog(body)
        elif self.dialog == "deck":
            self._draw_deck_dialog(body)
        elif self.dialog == "contracts":
            self._draw_contract_dialog(body)
        elif self.dialog == "contract_details":
            self._draw_contract_details(body)
        elif self.dialog == "shop":
            self._draw_shop_dialog(body)
        elif self.dialog == "projects":
            self._draw_project_dialog(body)
        elif self.dialog == "new_project":
            self._draw_new_project_dialog(body)
        elif self.dialog == "build_project":
            self._draw_build_project_dialog(body)
        elif self.dialog == "rest":
            self._draw_rest_dialog(body)
        elif self.dialog == "options":
            self._draw_options_dialog(body)
        elif self.dialog == "ice":
            self._draw_ice_dialog(body)
        elif self.dialog == "files":
            self._draw_file_dialog(body)
        elif self.dialog == "message":
            for index, line in enumerate(self.dialog_text):
                self._wrapped(line, pygame.Rect(body.left, body.top + index * 48, body.width, 44), self.font, TEXT)
        self._button(Button(pygame.Rect(rect.left + 15, rect.bottom - 43, 94, 29), "CLOSE", self.close_dialog))

    def _draw_new_dialog(self, body: pygame.Rect) -> None:
        self._text("Character name:", body.left, body.top, self.font, TEXT)
        input_rect = pygame.Rect(body.left, body.top + 28, body.width, 34)
        pygame.draw.rect(self.screen, PANEL_LIGHT, input_rect)
        pygame.draw.rect(self.screen, CYAN, input_rect, 1)
        self._text(self.text_input + ("_" if (pygame.time.get_ticks() // 500) % 2 else ""), input_rect.left + 8, input_rect.top + 8, self.font, WHITE)
        self._text("Character image:", body.left, body.top + 75, self.font, TEXT)
        try:
            sprite = self.assets.sprite("MISC_Characters.bmp", self.new_image, (24, 24))
            sprite.set_colorkey(sprite.get_at((0, 0)))
            self.screen.blit(pygame.transform.scale(sprite, (48, 48)), (body.left, body.top + 101))
        except FileNotFoundError:
            pass
        self._button(Button(pygame.Rect(body.left + 58, body.top + 106, 28, 28), "<", lambda: self.change_character_image(-1)))
        self._button(Button(pygame.Rect(body.left + 90, body.top + 106, 28, 28), ">", lambda: self.change_character_image(1)))
        self._button(Button(pygame.Rect(body.left + 135, body.top + 104, 128, 28),
                            f"TOOLTIPS: {'ON' if self.new_tooltips else 'OFF'}", self.toggle_new_tooltips))
        self._button(Button(pygame.Rect(body.left + 270, body.top + 104, 128, 28),
                            f"IRONMAN: {'ON' if self.new_ironman else 'OFF'}", self.toggle_new_ironman))
        self._text("Starting bonus:", body.left, body.top + 151, self.font, TEXT)
        options = (("none", "None"), ("skills", "Skills 2"), ("hardware", "Hardware 2"), ("software", "Software 2"), ("money", "2000 credits"))
        for index, (key, label) in enumerate(options):
            rect = pygame.Rect(body.left + (index % 3) * 148, body.top + 178 + (index // 3) * 42, 138, 32)
            self._button(Button(rect, ("> " if key == self.bonus else "") + label, lambda value=key: setattr(self, "bonus", value)))
        self._button(Button(pygame.Rect(body.right - 105, body.bottom - 2, 105, 30), "CREATE", self._create_character))

    def _draw_load_dialog(self, body: pygame.Rect) -> None:
        paths = self._save_files()
        if not paths:
            self._text("No Python save games found.", body.left, body.top + 12, self.font, DIM)
        else:
            for index, path in enumerate(paths[:11]):
                rect = pygame.Rect(body.left, body.top + index * 24, body.width, 22)
                if index == self.selection % len(paths[:11]):
                    pygame.draw.rect(self.screen, PANEL_LIGHT, rect)
                self._text(path.name, body.left + 6, body.top + 3 + index * 24, self.font_tiny, TEXT)
                self._button(Button(rect, "", lambda p=path: self._load_path(p)), transparent=True)

    def _draw_character_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        self._text(f"{char.name}  -  Reputation: {char.reputation}", body.left, body.top, self.font_big, WHITE)
        self._text(f"Credits: {char.credits}   Lifestyle: {LIFESTYLES[char.lifestyle]}   Skill points: {char.skill_points}", body.left, body.top + 34, self.font, CYAN)
        y = body.top + 68
        for index, (name, value) in enumerate(char.skills.items()):
            self._text(f"{name:14} {value}", body.left, y + index * 27, self.font, TEXT)
            self._button(Button(pygame.Rect(body.right - 40, y + index * 27 - 3, 34, 24), "+", lambda skill=name: self.improve_skill(skill), char.skill_points > 0))
        y = body.top + 238
        self._text("Chips: " + "  ".join(f"{name[:3]} {value}" for name, value in zip(CHIP_NAMES, char.chips)), body.left, y, self.font_tiny, DIM)
        self._text("Hardware: " + ", ".join(HARDWARE_NAMES[i] for i, value in enumerate(char.hardware) if value), body.left, y + 22, self.font_tiny, DIM)

    def _draw_deck_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        self._text(f"Load: {char.current_load}/{char.load_capacity}", body.left, body.top, self.font, CYAN)
        max_rows = 9
        widths = (42, 188, 56, 62)
        self._table_row(body.left, body.top + 24, widths, ("State", "Program", "Rating", "Size"), color=CYAN)
        for row, program in enumerate(char.programs[self.scroll:self.scroll + max_rows]):
            index = self.scroll + row
            state = ("L" if program.loaded else "-") + ("D" if program.load_default else "-")
            rect = self._table_row(
                body.left, body.top + 49 + row * 25, widths,
                (state, program.name, str(program.rating), f"{program.size} MP"),
                selected=index == self.selected_program, color=TEXT if program.loaded else DIM,
            )
            self._button(Button(rect, "", lambda i=index: self.select_program(i), tooltip=program.name), transparent=True)
        self._button(Button(pygame.Rect(body.right - 106, body.top + 28, 106, 30), "TOGGLE", self.load_program))
        self._button(Button(pygame.Rect(body.right - 106, body.top + 66, 106, 30), "DEFAULT", self.set_program_default))
        self._button(Button(pygame.Rect(body.right - 106, body.top + 104, 106, 30), "UNLOAD", self.unload_program))

    def _draw_contract_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        if char.current_contract:
            self._button(Button(pygame.Rect(body.left, body.top, 130, 32), "VIEW CONTRACT", self.view_current_contract))
            self._button(Button(pygame.Rect(body.left + 142, body.top, 130, 32), "ENTER MATRIX", self.enter_matrix))
            self._button(Button(pygame.Rect(body.left + 284, body.top, 130, 32), "ABANDON", self.abandon_contract))
            self._wrapped(char.current_contract.description, pygame.Rect(body.left, body.top + 50, body.width, body.height - 90), self.font, TEXT)
            if char.matrix:
                self._text(f"Status: {char.matrix.completed} of {char.matrix.target_count} objectives complete",
                           body.left, body.bottom - 26, self.font_tiny, CYAN)
            return
        if not char.contracts:
            self._text("No contracts are currently available.", body.left, body.top + 12, self.font, DIM)
            return
        widths = (118, 55, 153, 62, 55)
        self._table_row(body.left, body.top, widths, ("Type", "Diff", "Target", "Deadline", "Pay"), color=CYAN)
        for row, contract in enumerate(char.contracts[:9]):
            rect = self._table_row(
                body.left, body.top + 25 + row * 27, widths,
                (CONTRACT_TYPES[contract.contract_type], f"{contract.difficulty * 5}%",
                 f"{contract.system_name} ({contract.size})", f"{contract.days_left} days", f"{contract.pay}cr"),
                selected=row == self.selection,
            )
            self._button(Button(rect, "", lambda i=row: self.select_contract(i), tooltip=contract.description), transparent=True)
        self._button(Button(pygame.Rect(body.right - 100, body.bottom - 32, 100, 28), "VIEW",
                            self.view_selected_contract, char.contracts != []))

    def _draw_contract_details(self, body: pygame.Rect) -> None:
        assert self.character
        if self.selected_contract is None or self.selected_contract >= len(self.character.contracts):
            return
        contract = self.character.contracts[self.selected_contract]
        rows = (("Description", contract.description), ("Target corporation", f"{contract.system_name} ({contract.size})"),
                ("Type", CONTRACT_TYPES[contract.contract_type]), ("Difficulty", f"{contract.difficulty * 5}%"),
                ("Deadline", f"{contract.days_left} days"), ("Payment", f"{contract.pay} cr"))
        y = body.top
        for label, value in rows:
            self._text(label + ":", body.left, y, self.font_tiny, CYAN)
            self._wrapped(value, pygame.Rect(body.left + 115, y, body.width - 115, 52 if label == "Description" else 24), self.font_tiny, TEXT)
            y += 62 if label == "Description" else 31
        if self.character.current_contract is None:
            self._button(Button(pygame.Rect(body.right - 110, body.bottom - 34, 110, 30), "ACCEPT",
                                lambda: self.accept_contract(self.selected_contract or 0)))

    def _draw_shop_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        self._text(f"Credits: {char.credits}", body.left, body.top, self.font, CYAN)
        ordered = sorted(enumerate(char.shop), key=lambda pair: ({"software": 0, "hardware": 1, "chip": 2}[pair[1].item_type], pair[1].subtype, -pair[1].rating))
        widths = (72, 217, 75, 72)
        self._table_row(body.left, body.top + 27, widths, ("Class", "Item", "Cost", "Current"), color=CYAN)
        for row, (item_index, item) in enumerate(ordered[self.scroll:self.scroll + 9]):
            current = char.current_item_level(item.item_type, item.subtype)
            rect = self._table_row(
                body.left, body.top + 52 + row * 27, widths,
                (item.item_type.title(), item.description, f"{item.price}cr", str(current) if current else "-"),
                selected=item_index == self.selection,
            )
            self._button(Button(rect, "", lambda i=item_index: self.select_shop_item(i), tooltip=f"Purchase {item.description}"), transparent=True)
        self._button(Button(pygame.Rect(body.right - 100, body.bottom - 32, 100, 28), "PURCHASE", self.buy_selected_item,
                            bool(char.shop)))

    def _draw_project_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        project_text = "None"
        if char.project:
            project_text = f"{char.project.source_type} - {char.project.rating}"
        self._text("Current project", body.left, body.top, self.font_tiny, CYAN)
        self._text(project_text, body.left + 108, body.top, self.font, TEXT)
        self._text("Days left", body.left, body.top + 25, self.font_tiny, CYAN)
        self._text(str(char.project_time if char.project else "-"), body.left + 108, body.top + 25, self.font, TEXT)
        self._button(Button(pygame.Rect(body.right - 102, body.top, 102, 28), "NEW", self.show_new_project))
        self._button(Button(pygame.Rect(body.right - 102, body.top + 34, 102, 28), "WORK 1 DAY",
                            lambda: self.rest_project(1), char.project is not None))
        self._button(Button(pygame.Rect(body.right - 102, body.top + 68, 102, 28), "FINISH",
                            self.finish_project, char.project is not None))
        widths = (160, 70, 70, 92)
        self._table_row(body.left, body.top + 112, widths, ("Type", "Rating", "Current", "Source"), color=CYAN)
        for row, source in enumerate(char.source_code[:6]):
            current = (max((p.rating for p in char.programs if p.class_id == source.class_id), default=0)
                       if source.source_type == "software" else char.chips[source.class_id])
            rect = self._table_row(body.left, body.top + 137 + row * 27, widths,
                                   (source.source_type.title(), str(source.rating), str(current) if current else "-",
                                    PROGRAM_NAMES[source.class_id] if source.source_type == "software" else CHIP_NAMES[source.class_id]),
                                   selected=row == self.selected_source)
            self._button(Button(rect, "", lambda i=row: self.select_source(i)), transparent=True)
        self._button(Button(pygame.Rect(body.right - 102, body.bottom - 64, 102, 28), "BUILD",
                            self.show_build_project, bool(char.source_code)))
        self._button(Button(pygame.Rect(body.right - 102, body.bottom - 32, 102, 28), "TRASH",
                            self.trash_source, bool(char.source_code)))

    def _draw_new_project_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        classes = range(len(PROGRAM_NAMES) - 1) if self.project_type == "software" else range(len(CHIP_NAMES))
        self._button(Button(pygame.Rect(body.left, body.top, 130, 30), "SOFTWARE", lambda: self.change_project_type("software"),
                            image=None, hover_image=None, tooltip="Design program source"))
        self._button(Button(pygame.Rect(body.left + 140, body.top, 130, 30), "CHIP", lambda: self.change_project_type("chip"),
                            tooltip="Design chip source"))
        self._text("Type", body.left, body.top + 48, self.font_tiny, CYAN)
        for column, class_id in enumerate(classes):
            if class_id < self.project_class - (self.project_class % 6) or class_id >= self.project_class - (self.project_class % 6) + 6:
                continue
            label = PROGRAM_NAMES[class_id] if self.project_type == "software" else CHIP_NAMES[class_id]
            x = body.left + ((class_id % 6) % 3) * 148
            y = body.top + 70 + ((class_id % 6) // 3) * 31
            self._button(Button(pygame.Rect(x, y, 138, 27), label[:20], lambda c=class_id: self.change_project_class(c),
                                tooltip=label))
        self._button(Button(pygame.Rect(body.left + 300, body.top + 140, 34, 28), "<", lambda: self.change_project_class(max(0, self.project_class - 6))))
        self._button(Button(pygame.Rect(body.left + 338, body.top + 140, 34, 28), ">", lambda: self.change_project_class(min(max(classes), self.project_class + 6))))
        skill = self.character.skills["Programming"] if self.project_type == "software" else self.character.skills["Chip Design"]
        self._text(f"Skill {skill}", body.left, body.top + 145, self.font_tiny, DIM)
        self._text("Rating", body.left, body.top + 190, self.font_tiny, CYAN)
        for rating in range(1, skill + 1):
            self._button(Button(pygame.Rect(body.left + (rating - 1) * 37, body.top + 212, 32, 28), str(rating),
                                lambda r=rating: self.change_project_rating(r)))
        source = self.best_source(self.project_type, self.project_class)
        complexity = PROGRAM_COMPLEXITY[self.project_class] if self.project_type == "software" else self.project_class + 2
        work = max(1, complexity * self.project_rating * self.project_rating - complexity * source * source)
        days = (work + skill - 1) // skill
        self._text(f"Best source: {source}     Estimated time: {days} day(s)", body.left, body.bottom - 42, self.font_tiny, DIM)
        self._button(Button(pygame.Rect(body.right - 105, body.bottom - 34, 105, 30), "START", self.confirm_project))

    def _draw_build_project_dialog(self, body: pygame.Rect) -> None:
        self._text("Program name:", body.left, body.top, self.font, TEXT)
        self._button(Button(pygame.Rect(body.right - 105, body.top + 2, 105, 28), "NAME", self.edit_build_name))
        pygame.draw.rect(self.screen, PANEL_LIGHT, pygame.Rect(body.left, body.top + 28, body.width, 34))
        self._text(self.build_name + "_", body.left + 8, body.top + 37, self.font, WHITE)
        self._button(Button(pygame.Rect(body.left, body.top + 88, 160, 30),
                            f"LOAD: {'YES' if self.build_load else 'NO'}", self.toggle_build_load))
        self._button(Button(pygame.Rect(body.left, body.top + 128, 210, 30),
                            f"TRASH OLDER: {'YES' if self.build_trash else 'NO'}", self.toggle_build_trash,
                            self.build_load))
        self._button(Button(pygame.Rect(body.left + 220, body.top + 128, 210, 30),
                            f"UNLOAD OLDER: {'YES' if self.build_unload else 'NO'}", self.toggle_build_unload,
                            self.build_load))
        self._button(Button(pygame.Rect(body.right - 105, body.bottom - 34, 105, 30), "BUILD", self.build_source))

    def _draw_rest_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        self._text("Pass time, heal, and advance projects and orders.", body.left, body.top, self.font, TEXT)
        for index, days in enumerate((1, 3, 7, 14, 30)):
            self._button(Button(pygame.Rect(body.left + index * 89, body.top + 53, 80, 34), f"{days} DAY" + ("S" if days != 1 else ""), lambda d=days: self.rest(d)))
        self._text(f"Monthly cost at current lifestyle: {LIFESTYLE_COST[self.character.lifestyle]} credits.", body.left, body.top + 110, self.font_tiny, DIM)
        self._text("Most transitions also advance your active contract clocks.", body.left, body.top + 132, self.font_tiny, DIM)

    def _draw_options_dialog(self, body: pygame.Rect) -> None:
        assert self.character
        char = self.character
        self._button(Button(pygame.Rect(body.left, body.top, 220, 32), f"TOOLTIPS: {'ON' if char.tooltips else 'OFF'}", self.toggle_tooltips))
        self._button(Button(pygame.Rect(body.left, body.top + 42, 220, 32), f"IRONMAN: {'ON' if char.ironman else 'OFF'}", self.toggle_ironman))
        self._button(Button(pygame.Rect(body.left, body.top + 95, 220, 32), "SAVE GAME", self.save))
        self._button(Button(pygame.Rect(body.left, body.top + 137, 220, 32), "LOAD GAME", self.show_load))
        self._button(Button(pygame.Rect(body.left, body.top + 179, 220, 32), "NEW GAME", self.show_new_game))
        self._button(Button(pygame.Rect(body.left, body.top + 221, 220, 32), "RETURN TO TITLE", self.return_to_title))
        self._text("F5 or Ctrl+S: save", body.left + 250, body.top + 8, self.font_tiny, DIM)
        self._text("F9 or Ctrl+L: load", body.left + 250, body.top + 30, self.font_tiny, DIM)
        self._text("WASD: move in Matrix", body.left + 250, body.top + 52, self.font_tiny, DIM)
        self._text("Esc: close or disconnect", body.left + 250, body.top + 74, self.font_tiny, DIM)

    def _draw_file_dialog(self, body: pygame.Rect) -> None:
        assert self.character and self.character.matrix
        files = self.character.matrix.node.files
        widths = (242, 86, 62, 48)
        self._table_row(body.left, body.top, widths, ("File", "Type", "Size", "State"), color=CYAN)
        for index, file in enumerate(files):
            rect = self._table_row(
                body.left, body.top + 25 + index * 27, widths,
                (file.name, file.description, f"{file.size} MP", file.state),
                selected=index == self.selection, color=TEXT if file.state == "node" else DIM,
            )
            self._button(Button(rect, "", lambda i=index: self.select_file(i),
                                tooltip=file.description), transparent=True)
        self._button(Button(pygame.Rect(body.right - 120, body.bottom - 30, 120, 28),
                            self.file_action.upper(), self.perform_file_action,
                            bool(files)))

    def _draw_ice_dialog(self, body: pygame.Rect) -> None:
        assert self.character and self.character.matrix
        local = self.character.matrix.local_ice
        if not local:
            self._text("No ICE is present in this node.", body.left, body.top + 12, self.font, DIM)
            return
        self.selected_ice %= len(local)
        for index, ice in enumerate(local):
            rect = pygame.Rect(body.left, body.top + index * 30, body.width, 28)
            if index == self.selected_ice:
                pygame.draw.rect(self.screen, PANEL_LIGHT, rect)
            self._text(f"{ice.name:18} Rating {ice.rating:2}  Health {ice.health:3}  {'HOSTILE' if ice.hostile else 'PASSIVE'}", body.left + 5, body.top + 6 + index * 30, self.font_tiny, TEXT)
            self._button(Button(rect, "", lambda i=index: self.select_ice(i)), transparent=True)
        target = local[self.selected_ice]
        self._text("Analysis: " + (f"combat rating {target.combat_rating}, slow {target.slow_turns}, confuse {target.confuse_turns}" if target.analyzed else "unknown"), body.left, body.bottom - 45, self.font_tiny, YELLOW)

    def change_character_image(self, delta: int) -> None:
        self.new_image = (self.new_image + delta) % 17

    def toggle_new_tooltips(self) -> None:
        self.new_tooltips = not self.new_tooltips

    def toggle_new_ironman(self) -> None:
        self.new_ironman = not self.new_ironman

    def _create_character(self) -> None:
        if self.text_input.strip():
            self.character = Character.new(self.text_input.strip(), self.bonus)
            self.character.image = self.new_image
            self.character.ironman = self.new_ironman
            self.character.tooltips = self.new_tooltips
            self.scene = "home"
            self.close_dialog()
            self.assets.play("Map.wav")

    def _save_files(self) -> list[Path]:
        directory = default_save_directory()
        if not directory.exists():
            return []
        return sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)

    def _load_path(self, path: Path) -> None:
        try:
            self.character = load_game(path)
            self.scene = "matrix" if self.character.matrix else "home"
            self.close_dialog()
            self.show_message("GAME LOADED", f"Loaded {path.name}.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.show_message("LOAD FAILED", str(error))

    def show_new_game(self) -> None:
        self.text_input = "Hacker X"
        self.bonus = "none"
        self.new_image = 0
        self.new_ironman = False
        self.new_tooltips = True
        self.open_dialog("new", "CREATE CHARACTER")

    def show_load(self) -> None:
        self.open_dialog("load", "LOAD GAME")

    def quick_load(self) -> None:
        paths = self._save_files()
        if paths:
            self._load_path(paths[0])
        else:
            self.show_message("LOAD GAME", "No save games found.")

    def show_character(self) -> None:
        if self.character:
            self.open_dialog("character", "CHARACTER")

    def show_deck(self) -> None:
        if self.character:
            self.open_dialog("deck", "CYBERDECK")

    def show_contracts(self) -> None:
        if self.character:
            self.open_dialog("contracts", "CONTRACTS")

    def show_current_contract(self) -> None:
        self.show_contracts()

    def show_shop(self) -> None:
        if self.character:
            self.open_dialog("shop", "BLACK MARKET")

    def show_projects(self) -> None:
        if self.character:
            self.open_dialog("projects", "SOFTWARE PROJECTS")

    def show_rest(self) -> None:
        if self.character:
            self.open_dialog("rest", "REST")

    def show_options(self) -> None:
        if self.character:
            self.open_dialog("options", "OPTIONS")

    def show_ice(self) -> None:
        if self.character:
            self.open_dialog("ice", "ICE ANALYSIS")

    def _enter_dialog_selection(self) -> None:
        if self.dialog == "load":
            paths = self._save_files()
            if paths:
                self._load_path(paths[self.selection % len(paths)])

    def save(self) -> None:
        if not self.character:
            return
        try:
            path = save_game(self.character, quick_save_path(self.character))
            self.show_message("GAME SAVED", str(path))
        except OSError as error:
            self.show_message("SAVE FAILED", str(error))

    def quit(self) -> None:
        self.running = False

    def return_to_title(self) -> None:
        self.close_dialog()
        self.scene = "intro"

    def select_contract(self, index: int) -> None:
        self.selection = index

    def view_selected_contract(self) -> None:
        assert self.character
        if not self.character.contracts:
            return
        self.selected_contract = self.selection % len(self.character.contracts)
        self.open_dialog("contract_details", "CONTRACT DETAILS")

    def view_current_contract(self) -> None:
        assert self.character and self.character.current_contract
        self.dialog_title = "CONTRACT DETAILS"
        self.dialog_text = [self.character.current_contract.description]
        self.show_message("CONTRACT DETAILS", self.character.current_contract.description)

    def accept_contract(self, index: int) -> None:
        assert self.character
        self.character.accept_contract(index)
        self.open_dialog("contracts", "CONTRACT")

    def abandon_contract(self) -> None:
        assert self.character
        result = self.character.abandon_contract()
        self.show_message("CONTRACT", result)

    def select_shop_item(self, index: int) -> None:
        self.selection = index

    def buy_selected_item(self) -> None:
        if self.character and self.character.shop:
            self.buy_item(self.selection % len(self.character.shop))

    def buy_item(self, index: int) -> None:
        assert self.character
        if 0 <= index < len(self.character.shop):
            result = self.character.buy(index)
            self.show_message("BLACK MARKET", result)

    def improve_skill(self, skill: str) -> None:
        assert self.character
        if self.character.skill_points > 0:
            self.character.skills[skill] += 1
            self.character.skill_points -= 1

    def select_source(self, index: int) -> None:
        self.selected_source = index

    def show_new_project(self) -> None:
        self.project_type = "software"
        self.project_class = 0
        self.project_rating = max(1, self.character.skills["Programming"] if self.character else 1)
        self.open_dialog("new_project", "NEW PROJECT")

    def change_project_type(self, project_type: str) -> None:
        self.project_type = project_type
        self.project_class = 0
        skill = self.character.skills["Programming" if project_type == "software" else "Chip Design"] if self.character else 1
        self.project_rating = min(self.project_rating, skill)

    def change_project_class(self, class_id: int) -> None:
        limit = len(PROGRAM_NAMES) - 2 if self.project_type == "software" else len(CHIP_NAMES) - 1
        self.project_class = max(0, min(limit, class_id))

    def change_project_rating(self, rating: int) -> None:
        self.project_rating = rating

    def best_source(self, project_type: str, class_id: int) -> int:
        assert self.character
        return max((source.rating for source in self.character.source_code
                    if source.source_type == project_type and source.class_id == class_id), default=0)

    def confirm_project(self) -> None:
        assert self.character
        skill = self.character.skills["Programming" if self.project_type == "software" else "Chip Design"]
        source = self.best_source(self.project_type, self.project_class)
        complexity = PROGRAM_COMPLEXITY[self.project_class] if self.project_type == "software" else self.project_class + 2
        work = complexity * self.project_rating ** 2 - complexity * source ** 2
        if work <= 0:
            work = max(1, complexity * (source - self.project_rating))
        self.character.project = SourceCode(self.project_type, self.project_class, self.project_rating)
        self.character.project_time = max(1, (work + skill - 1) // skill)
        self.open_dialog("projects", "SOFTWARE PROJECTS")

    def rest_project(self, days: int) -> None:
        assert self.character
        if not self.character.project:
            return
        self.character.advance_project(days)
        self.character.rest(days)
        self.open_dialog("projects", "SOFTWARE PROJECTS")

    def finish_project(self) -> None:
        assert self.character
        if self.character.project:
            skill_name = "Programming" if self.character.project.source_type == "software" else "Chip Design"
            skill = self.character.skills[skill_name] * (1 + self.character.hardware[7])
            days = max(1, (self.character.project_time + skill - 1) // skill)
            self.character.advance_project(days)
            self.character.rest(days)
            self.open_dialog("projects", "SOFTWARE PROJECTS")

    def show_build_project(self) -> None:
        assert self.character
        if not self.character.source_code:
            return
        source = self.character.source_code[self.selected_source % len(self.character.source_code)]
        if source.source_type != "software":
            result = self.build_chip(source)
            self.show_message("CHIP BURNER", result)
            return
        self.build_name = f"{PROGRAM_NAMES[source.class_id]} {source.rating}"
        self.build_load = True
        self.build_trash = True
        self.build_unload = False
        self.open_dialog("build_project", "BUILD PROGRAM")

    def edit_build_name(self) -> None:
        pass

    def toggle_build_load(self) -> None:
        self.build_load = not self.build_load
        if not self.build_load:
            self.build_trash = self.build_unload = False

    def toggle_build_trash(self) -> None:
        if self.build_load:
            self.build_trash = not self.build_trash
            if self.build_trash:
                self.build_unload = False

    def toggle_build_unload(self) -> None:
        if self.build_load:
            self.build_unload = not self.build_unload
            if self.build_unload:
                self.build_trash = False

    def build_source(self) -> None:
        assert self.character
        if not self.build_name.strip() or not self.character.source_code:
            return
        source = self.character.source_code[self.selected_source % len(self.character.source_code)]
        old = [p for p in self.character.programs if p.class_id == source.class_id and p.rating <= source.rating]
        program = Program(source.class_id, source.rating, self.build_name.strip(), self.build_load, self.build_load)
        self.character.programs.append(program)
        if self.build_load:
            self.character.programs.sort(key=lambda item: (item.class_id, -item.rating))
        if self.build_trash:
            for item in old:
                if item in self.character.programs:
                    self.character.programs.remove(item)
        elif self.build_unload:
            for item in old:
                item.loaded = item.load_default = False
        self.open_dialog("projects", "SOFTWARE PROJECTS")
        self.show_message("PROGRAM BUILT", "Program has been compiled and is now available for use.")

    def build_chip(self, source: SourceCode) -> str:
        assert self.character
        if not self.character.hardware[0]:
            return "You do not own a chip burner."
        if self.character.chips[source.class_id] >= source.rating:
            return "This chip is lower than what is already installed."
        self.character.chips[source.class_id] = source.rating
        return f"{CHIP_NAMES[source.class_id]} Level {source.rating} installed."

    def trash_source(self) -> None:
        assert self.character
        if self.character.source_code:
            self.character.source_code.pop(self.selected_source % len(self.character.source_code))

    def rest(self, days: int) -> None:
        assert self.character
        result = self.character.rest(days)
        self.show_message("REST", result)

    def _rest_selected_days(self) -> None:
        self.rest((1, 3, 7, 14, 30)[self.selection % 5])

    def toggle_tooltips(self) -> None:
        assert self.character
        self.character.tooltips = not self.character.tooltips

    def toggle_ironman(self) -> None:
        assert self.character
        self.character.ironman = not self.character.ironman

    def select_program(self, index: int) -> None:
        assert self.character
        if 0 <= index < len(self.character.programs):
            self.selected_program = index

    def selected_program_object(self) -> Program | None:
        if not self.character or not self.character.programs:
            return None
        self.selected_program %= len(self.character.programs)
        return self.character.programs[self.selected_program]

    def load_program(self) -> None:
        program = self.selected_program_object()
        if not program or not self.character:
            return
        if program.loaded:
            program.loaded = False
        elif self.character.current_load + program.size <= self.character.load_capacity:
            program.loaded = True
        else:
            self.show_message("CYBERDECK", "That program would overload the deck.")

    def unload_program(self) -> None:
        program = self.selected_program_object()
        if program:
            program.loaded = False

    def set_program_default(self) -> None:
        program = self.selected_program_object()
        if program and program.class_id in (0, 1, 2):
            for candidate in self.character.programs if self.character else ():
                if candidate.class_id in (0, 1, 2):
                    candidate.load_default = False
            program.load_default = True
            if self.character and self.character.matrix:
                self.character.matrix.post(f"{program.name} is now the default attack program.")

    def enter_matrix(self) -> None:
        if not self.character:
            return
        result = self.character.start_matrix()
        if self.character.matrix:
            self.scene = "matrix"
            self.close_dialog()
            self.assets.play("EnterMatrix.wav")
            if self.character.matrix.messages:
                self.character.matrix.messages[0] = result
        else:
            self.show_message("MATRIX", result)

    def disconnect(self) -> None:
        if not self.character or not self.character.matrix:
            return
        self.character.matrix.disconnected = True
        result = self.character.finish_matrix()
        self.scene = "home"
        self.show_message("DISCONNECTED", result)

    def move(self, direction: str) -> None:
        if self.character and self.character.matrix:
            self.character.matrix.move(direction)
            self.assets.play("Move.wav")
            self.check_run_state()

    def wait_turn(self) -> None:
        if self.character and self.character.matrix:
            self.character.matrix.tick()
            self.check_run_state()

    def matrix_attack(self) -> None:
        if self.character and self.character.matrix:
            program = next((p for p in self.character.programs
                            if p.loaded and p.load_default and p.class_id in (0, 1, 2)), None)
            if program is None:
                self.show_message("ATTACK", "No default attack program specified.")
                return
            local = self.character.matrix.local_ice
            target = local[self.selected_ice] if local and self.selected_ice < len(local) else None
            self.character.matrix.attack(program, target)
            self.assets.play("Zap.wav")
            self.check_run_state()

    def matrix_deceive(self) -> None:
        if self.character and self.character.matrix:
            program = next((p for p in self.character.programs if p.loaded and p.class_id == 14), None)
            if program:
                self.character.matrix.run_program(program)
                self.assets.play("Deceive.wav")
            else:
                self.show_message("DECEIVE", "No loaded Deceive program.")

    def matrix_scan(self) -> None:
        if self.character and self.character.matrix:
            program = next((p for p in self.character.programs if p.loaded and p.class_id == 17), None)
            if program:
                self.character.matrix.run_program(program)
                self.assets.play("Scan.wav")
            else:
                self.show_message("SCAN", "No loaded Scan program.")

    def run_selected_program(self) -> None:
        if not self.character or not self.character.matrix:
            return
        program = self.selected_program_object()
        if not program or not program.loaded:
            self.show_message("PROGRAM", "The selected program is not loaded.")
            return
        local = self.character.matrix.local_ice
        target: Ice | None = local[self.selected_ice] if local and self.selected_ice < len(local) else None
        self.character.matrix.run_program(program, target)
        if program.class_id in (5, 16, 17):
            sounds = {5: "Silence.wav", 16: "Analyze.wav", 17: "Scan.wav"}
            self.assets.play(sounds[program.class_id])
        self.check_run_state()

    def select_ice(self, index: int) -> None:
        self.selected_ice = index

    def select_file(self, index: int) -> None:
        self.selection = index

    def perform_file_action(self) -> None:
        if not self.character or not self.character.matrix:
            return
        files = self.character.matrix.node.files
        if not files:
            return
        self.character.matrix.use_node(self.file_action, self.selection % len(files))
        self.close_dialog()
        self.check_run_state()

    def node_action(self, action: str) -> None:
        if self.character and self.character.matrix:
            if action in ("download", "edit", "erase"):
                if not self.character.matrix.node.files:
                    self.character.matrix.post("This datastore contains no accessible files.")
                    return
                self.file_action = action
                self.open_dialog("files", "DATASTORE FILES")
                return
            self.character.matrix.use_node(action)
            if action == "crash":
                self.assets.play("Crash.wav")
            elif action == "map":
                self.assets.play("Map.wav")
            elif action == "backdoor":
                self.assets.play("Backdoor.wav")
            elif action == "download":
                self.assets.play("StartDownload.wav")
            self.check_run_state()

    def check_run_state(self) -> None:
        assert self.character and self.character.matrix
        if self.character.matrix.crashed:
            result = self.character.finish_matrix()
            self.scene = "home"
            self.show_message("CONNECTION LOST", result)
        elif self.character.matrix.complete():
            self.show_message("OBJECTIVE COMPLETE", "The contract objective is complete. Disconnect to collect your payment.")


def find_repository_root(start: Path) -> Path:
    candidates = (start, start.parent, start.parent.parent, Path.cwd())
    for candidate in candidates:
        if (candidate / "DefaultGraphics").is_dir() and (candidate / "Sound").is_dir():
            return candidate
    return start


def main() -> int:
    root = find_repository_root(Path(__file__).resolve().parent)
    return DeckerApp(root).run()
