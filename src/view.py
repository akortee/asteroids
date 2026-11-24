"""Модуль отрисовки и работы с графическими ресурсами игры."""

from __future__ import annotations

import math
from pathlib import Path

import pygame

from src.config import (
    ASTEROID_PATHS,
    BG_DYNAMIC_ALPHA,
    BG_DYNAMIC_PATH,
    BG_STATIC_PATH,
    EXPLOSION_PATH,
    SHIP_IDLE_PATH,
    SHIP_RADIUS,
    SHIP_THRUST_PATH,
    SPLASH_RECT,
)
from src.models import Asteroid, Explosion, GameModel, Missile, Ship
from src.models import deg_to_vec


def _load_image(
    path: Path,
    size: tuple[int, int],
    fallback_color: tuple[int, int, int, int],
    use_alpha: bool = True,
) -> pygame.Surface:
    """Загружает картинку и масштабирует её; при ошибке создаёт заглушку."""
    if path.exists():
        raw = pygame.image.load(str(path))
        surf = raw.convert_alpha() if use_alpha else raw.convert()
        return pygame.transform.smoothscale(surf, size)

    surf = pygame.Surface(size, pygame.SRCALPHA if use_alpha else 0)
    surf.fill(fallback_color)
    return surf


class GameView:
    """Отрисовывает фон, спрайты, взрывы, заставку и показатели игры."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Инициализирует ресурсы, шрифты и поверхность экрана."""
        self.screen: pygame.Surface = screen
        self.width: int = screen.get_width()
        self.height: int = screen.get_height()

        self.static_bg: pygame.Surface = _load_image(
            BG_STATIC_PATH,
            (self.width, self.height),
            (10, 12, 24, 255),
            use_alpha=False,
        )
        dynamic_raw = _load_image(
            BG_DYNAMIC_PATH,
            (self.width, self.height),
            (160, 165, 180, 255),
            use_alpha=True,
        )
        self.dynamic_bg: pygame.Surface = dynamic_raw.copy()
        self.dynamic_bg.set_alpha(BG_DYNAMIC_ALPHA)

        ship_box = int(SHIP_RADIUS * 3.0)
        self.ship_idle: pygame.Surface = _load_image(
            SHIP_IDLE_PATH,
            (ship_box, ship_box),
            (220, 225, 235, 255),
        )
        self.ship_thrust: pygame.Surface = _load_image(
            SHIP_THRUST_PATH,
            (ship_box, ship_box),
            (255, 165, 60, 255),
        )

        self.asteroid_sprites: list[pygame.Surface] = [
            _load_image(
                ast_path,
                (96, 96),
                (130, 130, 140, 255),
            )
            for ast_path in ASTEROID_PATHS
        ]
        if not self.asteroid_sprites:
            fallback_ast = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.circle(fallback_ast, (130, 130, 140, 255), (48, 48), 44)
            self.asteroid_sprites = [fallback_ast]

        self.explosion_sprite: pygame.Surface = _load_image(
            EXPLOSION_PATH,
            (128, 128),
            (255, 150, 40, 220),
        )

        self.hud_font: pygame.font.Font = pygame.font.SysFont(
            "arial",
            26,
            bold=True,
        )
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "arial",
            34,
            bold=True,
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "arial",
            20,
            bold=True,
        )

    def _draw_dynamic_bg(self, scroll_x: float) -> None:
        """Рисует полупрозрачный слой астероидов, сдвигающийся влево."""
        shift = int(scroll_x) % self.width
        self.screen.blit(self.dynamic_bg, (-shift, 0))
        self.screen.blit(self.dynamic_bg, (self.width - shift, 0))

    def _draw_ship(self, ship: Ship) -> None:
        """Рисует корабль с учётом поворота и включения двигателей."""
        sprite = self.ship_thrust if ship.thrusting else self.ship_idle
        # Отрицательный угол соответствует повороту по часовой стрелке в pygame
        rotated = pygame.transform.rotate(sprite, -(ship.angle + 90.0))
        rect = rotated.get_rect(center=(int(ship.x), int(ship.y)))
        self.screen.blit(rotated, rect)

    def _draw_asteroid(self, asteroid: Asteroid) -> None:
        """Рисует спрайт астероида, смасштабированный под его радиус."""
        base_img = self.asteroid_sprites[
            asteroid.sprite_index % len(self.asteroid_sprites)
        ]
        diameter = max(8, int(asteroid.radius * 2.0))
        scaled = pygame.transform.smoothscale(base_img, (diameter, diameter))
        rotated = pygame.transform.rotate(scaled, -asteroid.angle)
        rect = rotated.get_rect(center=(int(asteroid.x), int(asteroid.y)))
        self.screen.blit(rotated, rect)

    def _draw_missile(self, missile: Missile) -> None:
        """Рисует летящую ракету."""
        dx, dy = deg_to_vec(missile.angle)
        x1 = int(missile.x - dx * 8.0)
        y1 = int(missile.y - dy * 8.0)
        x2 = int(missile.x + dx * 6.0)
        y2 = int(missile.y + dy * 6.0)
        pygame.draw.line(self.screen, (255, 225, 90), (x1, y1), (x2, y2), 4)

    def _draw_explosion(self, explosion: Explosion) -> None:
        """Рисует спрайт взрыва на месте уничтоженного объекта."""
        scale = 0.5 + math.sin(explosion.progress * math.pi) * 0.9
        size = max(12, int(explosion.radius * 2.4 * scale))
        scaled = pygame.transform.smoothscale(
            self.explosion_sprite,
            (size, size),
        )
        alpha = max(0, int(255 * (1.0 - explosion.progress)))
        frame = scaled.copy()
        frame.set_alpha(alpha)
        rect = frame.get_rect(center=(int(explosion.x), int(explosion.y)))
        self.screen.blit(frame, rect)

    def _draw_hud(self, model: GameModel) -> None:
        """Отрисовывает количество жизней и очков."""
        lives_surf = self.hud_font.render(
            f"Lives: {model.lives}",
            True,
            (80, 240, 90),
        )
        score_surf = self.hud_font.render(
            f"Score: {model.score}",
            True,
            (80, 240, 90),
        )
        self.screen.blit(lives_surf, (20, 14))
        self.screen.blit(
            score_surf,
            (self.width - score_surf.get_width() - 20, 14),
        )

    def _draw_splash(self, title: str) -> None:
        """Отрисовывает прямоугольник заставки по центру экрана."""
        left, top, width, height = SPLASH_RECT
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((20, 30, 70, 215))
        self.screen.blit(panel, (left, top))
        pygame.draw.rect(
            self.screen,
            (110, 155, 255),
            pygame.Rect(left, top, width, height),
            width=3,
        )

        title_surf = self.title_font.render(title, True, (255, 255, 255))
        hint_surf = self.hint_font.render(
            "CLICK TO START",
            True,
            (220, 235, 255),
        )
        cx = left + width // 2
        cy = top + height // 2
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 22)))
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, cy + 24)))

    def draw(self, model: GameModel) -> None:
        """Отрисовывает текущий кадр игры."""
        self.screen.blit(self.static_bg, (0, 0))
        self._draw_dynamic_bg(model.bg_scroll_x)

        if model.state == "playing":
            for asteroid in model.asteroids:
                self._draw_asteroid(asteroid)
            for missile in model.missiles:
                self._draw_missile(missile)
            self._draw_ship(model.ship)

        for explosion in model.explosions:
            self._draw_explosion(explosion)

        self._draw_hud(model)

        if model.state == "splash":
            self._draw_splash("ASTEROIDS")
        elif model.state == "gameover":
            self._draw_splash("GAME OVER")
