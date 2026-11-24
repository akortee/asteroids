"""Модуль главного цикла и обработки событий приложения."""

from __future__ import annotations

import pygame

from src.config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from src.models import GameModel
from src.view import GameView


def _read_input() -> tuple[int, bool, bool]:
    """Считывает нажатия клавиш управления кораблём и стрельбой."""
    keys = pygame.key.get_pressed()
    turn_dir = 0
    if keys[pygame.K_LEFT]:
        turn_dir -= 1
    if keys[pygame.K_RIGHT]:
        turn_dir += 1
    thrust_on = bool(keys[pygame.K_UP])
    fire_pressed = bool(keys[pygame.K_SPACE])
    return turn_dir, thrust_on, fire_pressed


class GameApp:
    """Управляет окном Pygame, циклом событий и обновлением кадра."""

    def __init__(self) -> None:
        """Инициализирует окно, модель и представление игры."""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.model: GameModel = GameModel()
        self.view: GameView = GameView(self.screen)

    def run(self) -> None:
        """Запускает главный цикл игры до закрытия окна."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    self.model.on_mouse_click(event.pos)

            turn_dir, thrust_on, fire_pressed = _read_input()
            self.model.update(dt, turn_dir, thrust_on, fire_pressed)
            self.view.draw(self.model)
            pygame.display.flip()

        pygame.quit()
