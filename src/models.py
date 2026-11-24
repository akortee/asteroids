"""Модели объектов, математика и игровая логика «Астероидов»."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from src.config import (
    ASTEROID_MAX_COUNT,
    ASTEROID_MAX_RADIUS,
    ASTEROID_MAX_SPEED,
    ASTEROID_MAX_SPIN,
    ASTEROID_MIN_RADIUS,
    ASTEROID_MIN_SPEED,
    ASTEROID_MIN_SPIN,
    ASTEROID_PATHS,
    ASTEROID_SPAWN_INTERVAL,
    BG_SCROLL_SPEED,
    EXPLOSION_DURATION,
    FIRE_COOLDOWN,
    INITIAL_LIVES,
    INITIAL_SCORE,
    MISSILE_LIFETIME,
    MISSILE_RADIUS,
    MISSILE_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIP_DRAG,
    SHIP_RADIUS,
    SHIP_THRUST,
    SHIP_TURN_SPEED,
    SPLASH_RECT,
)


def deg_to_vec(angle_deg: float) -> tuple[float, float]:
    """Переводит угол в градусах в единичный вектор направления (dx, dy)."""
    rad = math.radians(angle_deg)
    return math.cos(rad), math.sin(rad)


def wrap_torus(
    x: float,
    y: float,
    width: int = SCREEN_WIDTH,
    height: int = SCREEN_HEIGHT,
) -> tuple[float, float]:
    """Замыкает координаты на тороидальном поле при выходе за границы."""
    return x % width, y % height


def hit_circles(
    x1: float,
    y1: float,
    r1: float,
    x2: float,
    y2: float,
    r2: float,
) -> bool:
    """Проверяет столкновение двух объектов по сумме их радиусов."""
    return math.hypot(x1 - x2, y1 - y2) <= (r1 + r2)


def click_in_splash(pos: tuple[int, int]) -> bool:
    """Проверяет, находится ли точка клика внутри прямоугольника заставки."""
    left, top, width, height = SPLASH_RECT
    px, py = pos
    return left <= px <= left + width and top <= py <= top + height


@dataclass
class Ship:
    """Корабль игрока с вращением, тягой и затуханием скорости."""

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    angle: float = -90.0
    radius: float = SHIP_RADIUS
    thrusting: bool = False

    def reset_center(self) -> None:
        """Размещает неподвижный корабль в центре игрового поля."""
        self.x = SCREEN_WIDTH / 2.0
        self.y = SCREEN_HEIGHT / 2.0
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -90.0
        self.thrusting = False

    def step(self, dt: float, turn_dir: int, thrust_on: bool) -> None:
        """Обновляет ориентацию, скорость и координаты корабля за шаг dt."""
        self.angle = (self.angle + turn_dir * SHIP_TURN_SPEED * dt) % 360.0
        self.thrusting = thrust_on

        dx, dy = deg_to_vec(self.angle)
        if thrust_on:
            self.vx += dx * SHIP_THRUST * dt
            self.vy += dy * SHIP_THRUST * dt

        # Плавное замедление корабля при выключенном двигателе
        damping = math.exp(-SHIP_DRAG * dt)
        self.vx *= damping
        self.vy *= damping
        if not thrust_on and math.hypot(self.vx, self.vy) < 0.2:
            self.vx = 0.0
            self.vy = 0.0

        self.x, self.y = wrap_torus(
            self.x + self.vx * dt,
            self.y + self.vy * dt,
        )


@dataclass
class Asteroid:
    """Астероид со случайной линейной и угловой скоростью."""

    x: float
    y: float
    vx: float
    vy: float
    angle: float
    spin: float
    radius: float
    sprite_index: int

    def step(self, dt: float) -> None:
        """Перемещает и вращает астероид на тороидальном поле."""
        self.angle = (self.angle + self.spin * dt) % 360.0
        self.x, self.y = wrap_torus(
            self.x + self.vx * dt,
            self.y + self.vy * dt,
        )


@dataclass
class Missile:
    """Ракета с постоянной скоростью и ограниченным временем жизни."""

    x: float
    y: float
    vx: float
    vy: float
    angle: float
    ttl: float
    radius: float = MISSILE_RADIUS

    def step(self, dt: float) -> bool:
        """Сдвигает ракету и уменьшает таймер жизни; False при истечении."""
        self.ttl -= dt
        if self.ttl <= 0.0:
            return False
        self.x, self.y = wrap_torus(
            self.x + self.vx * dt,
            self.y + self.vy * dt,
        )
        return True


@dataclass
class Explosion:
    """Анимация взрыва на месте уничтоженного объекта."""

    x: float
    y: float
    radius: float
    elapsed: float = 0.0
    duration: float = EXPLOSION_DURATION

    def step(self, dt: float) -> bool:
        """Продвигает время анимации взрыва; False по завершении."""
        self.elapsed += dt
        return self.elapsed < self.duration

    @property
    def progress(self) -> float:
        """Возвращает долю прошедшего времени анимации в диапазоне [0.0,1.0]"""
        return min(1.0, self.elapsed / self.duration)


class GameModel:
    """Управляет состояниями игры, сущностями, столкновениями и счётом."""

    def __init__(self) -> None:
        """Создаёт начальное состояние игры с 3 жизнями и 0 очков."""
        self.state: str = "splash"  # "splash" | "playing" | "gameover"
        self.lives: int = INITIAL_LIVES
        self.score: int = INITIAL_SCORE
        self.bg_scroll_x: float = 0.0
        self.ship: Ship = Ship(x=SCREEN_WIDTH / 2.0, y=SCREEN_HEIGHT / 2.0)
        self.asteroids: list[Asteroid] = []
        self.missiles: list[Missile] = []
        self.explosions: list[Explosion] = []
        self._spawn_timer: float = 0.0
        self._fire_timer: float = 0.0

    def start_game(self) -> None:
        """Начинает новый раунд: центр корабля, сброс счёта и жизней."""
        self.state = "playing"
        self.lives = INITIAL_LIVES
        self.score = INITIAL_SCORE
        self.ship.reset_center()
        self.asteroids.clear()
        self.missiles.clear()
        self.explosions.clear()
        self._spawn_timer = ASTEROID_SPAWN_INTERVAL
        self._fire_timer = 0.0
        self._spawn_asteroid()

    def on_mouse_click(self, pos: tuple[int, int]) -> None:
        """Обрабатывает клик мыши: запускает игру только по заставке."""
        if self.state == "splash" and click_in_splash(pos):
            self.start_game()

    def _spawn_asteroid(self) -> None:
        """Создаёт астероид в случайной точке со случайными скоростями."""
        if len(self.asteroids) >= ASTEROID_MAX_COUNT:
            return

        radius = random.uniform(ASTEROID_MIN_RADIUS, ASTEROID_MAX_RADIUS)
        # Отступаем от корабля при появлении, чтобы не убить игрока мгновенно
        while True:
            x = random.uniform(0.0, float(SCREEN_WIDTH))
            y = random.uniform(0.0, float(SCREEN_HEIGHT))
            if math.hypot(x - self.ship.x, y - self.ship.y) > radius + 85.0:
                break

        move_angle = random.uniform(0.0, 360.0)
        speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)
        dx, dy = deg_to_vec(move_angle)
        spin = random.uniform(ASTEROID_MIN_SPIN, ASTEROID_MAX_SPIN)
        sprite_idx = random.randrange(max(1, len(ASTEROID_PATHS)))

        self.asteroids.append(
            Asteroid(
                x=x,
                y=y,
                vx=dx * speed,
                vy=dy * speed,
                angle=random.uniform(0.0, 360.0),
                spin=spin,
                radius=radius,
                sprite_index=sprite_idx,
            )
        )

    def _spawn_missile(self) -> None:
        """Выпускает ракету из носа корабля по направлению его ориентации."""
        if self._fire_timer > 0.0:
            return
        dx, dy = deg_to_vec(self.ship.angle)
        offset = self.ship.radius + MISSILE_RADIUS + 2.0
        mx, my = wrap_torus(self.ship.x + dx * offset, self.ship.y + dy*offset)
        self.missiles.append(
            Missile(
                x=mx,
                y=my,
                vx=dx * MISSILE_SPEED,
                vy=dy * MISSILE_SPEED,
                angle=self.ship.angle,
                ttl=MISSILE_LIFETIME,
            )
        )
        self._fire_timer = FIRE_COOLDOWN

    def update(
        self,
        dt: float,
        turn_dir: int,
        thrust_on: bool,
        fire_pressed: bool,
    ) -> None:
        """Выполняет шаг моделирования игры за интервал времени dt."""
        # Динамический фон движется влево с постоянной скоростью
        self.bg_scroll_x = (
            self.bg_scroll_x + BG_SCROLL_SPEED * dt
        ) % SCREEN_WIDTH

        if self.state != "playing":
            return

        if self._fire_timer > 0.0:
            self._fire_timer = max(0.0, self._fire_timer - dt)

        self._spawn_timer -= dt
        if self._spawn_timer <= 0.0:
            self._spawn_asteroid()
            self._spawn_timer = ASTEROID_SPAWN_INTERVAL

        self.ship.step(dt, turn_dir, thrust_on)
        if fire_pressed:
            self._spawn_missile()

        # Астероиды не сталкиваются друг с другом и проходят сквозь друг друга
        for asteroid in self.asteroids:
            asteroid.step(dt)

        kept_missiles: list[Missile] = []
        destroyed_asteroids: set[int] = set()

        for missile in self.missiles:
            if not missile.step(dt):
                continue
            hit_any = False
            for idx, asteroid in enumerate(self.asteroids):
                if idx in destroyed_asteroids:
                    continue
                if hit_circles(
                    missile.x,
                    missile.y,
                    missile.radius,
                    asteroid.x,
                    asteroid.y,
                    asteroid.radius,
                ):
                    hit_any = True
                    destroyed_asteroids.add(idx)
                    self.score += 1
                    self.explosions.append(
                        Explosion(
                            x=asteroid.x,
                            y=asteroid.y,
                            radius=asteroid.radius,
                        )
                    )
                    break
            if not hit_any:
                kept_missiles.append(missile)

        self.missiles = kept_missiles
        if destroyed_asteroids:
            self.asteroids = [
                ast
                for idx, ast in enumerate(self.asteroids)
                if idx not in destroyed_asteroids
            ]

        remaining_asteroids: list[Asteroid] = []
        for asteroid in self.asteroids:
            if hit_circles(
                self.ship.x,
                self.ship.y,
                self.ship.radius * 0.85,
                asteroid.x,
                asteroid.y,
                asteroid.radius,
            ):
                self.explosions.append(
                    Explosion(
                        x=asteroid.x,
                        y=asteroid.y,
                        radius=asteroid.radius,
                    )
                )
                self.lives -= 1
                if self.lives <= 0:
                    self.lives = 0
                    self.state = "gameover"
                    self.missiles.clear()
                    remaining_asteroids.clear()
                    break
                self.ship.reset_center()
            else:
                remaining_asteroids.append(asteroid)

        if self.state == "playing":
            self.asteroids = remaining_asteroids

        self.explosions = [exp for exp in self.explosions if exp.step(dt)]
