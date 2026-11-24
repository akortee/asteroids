"""Глобальные параметры и константы игры «Астероиды»."""

from pathlib import Path

# Пути к директории ресурсов и файлам изображений
BASE_DIR: Path = Path(__file__).resolve().parent.parent
ASSETS_DIR: Path = BASE_DIR / "assets"

BG_STATIC_PATH: Path = ASSETS_DIR / "nebula.jpg"
BG_DYNAMIC_PATH: Path = ASSETS_DIR / "debris.png"
SHIP_IDLE_PATH: Path = ASSETS_DIR / "ship.png"
SHIP_THRUST_PATH: Path = ASSETS_DIR / "ship_thrust.png"
EXPLOSION_PATH: Path = ASSETS_DIR / "explosion.png"
ASTEROID_PATHS: tuple[Path, ...] = (
    ASSETS_DIR / "asteroid_0.png",
    ASSETS_DIR / "asteroid_1.png",
    ASSETS_DIR / "asteroid_2.png",
)

# Параметры окна и частоты кадров
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
FPS: int = 60
WINDOW_TITLE: str = "Астероиды"

# Начальные значения жизней и очков
INITIAL_LIVES: int = 3
INITIAL_SCORE: int = 0

# Параметры динамического фона (смещение влево с постоянной скоростью)
BG_SCROLL_SPEED: float = 50.0  # Пикселей в секунду влево
BG_DYNAMIC_ALPHA: int = 95  # Прозрачность слоя фоновых астероидов (0..255)

# Параметры корабля и сопротивления среды
SHIP_RADIUS: float = 20.0
SHIP_TURN_SPEED: float = 240.0  # Угловая скорость поворота (градусов/сек)
SHIP_THRUST: float = 260.0  # Линейное ускорение при тяге (px/s^2)
SHIP_DRAG: float = 1.8  # Коэффициент затухания скорости без тяги

# Параметры ракет
MISSILE_SPEED: float = 500.0  # Постоянная скорость полёта ракеты (px/s)
MISSILE_RADIUS: float = 4.0
FIRE_COOLDOWN: float = 0.22  # Минимальный интервал между выстрелами (сек)
# Ракета не должна пролетать всё поле даже по малому измерению:
# T_cross = min(SCREEN_WIDTH, SCREEN_HEIGHT) / MISSILE_SPEED.
# Задаём время жизни строго меньше T_cross (0.65 от полного пролёта).
MISSILE_LIFETIME: float = (
    0.65 * (min(SCREEN_WIDTH, SCREEN_HEIGHT) / MISSILE_SPEED)
)

# Параметры генерации и движения астероидов
ASTEROID_SPAWN_INTERVAL: float = 1.25  # Частота появления астероидов (сек)
ASTEROID_MAX_COUNT: int = 16
ASTEROID_MIN_RADIUS: float = 22.0
ASTEROID_MAX_RADIUS: float = 44.0
ASTEROID_MIN_SPEED: float = 45.0
ASTEROID_MAX_SPEED: float = 140.0
ASTEROID_MIN_SPIN: float = -120.0  # Угловая скорость вращения (град/сек)
ASTEROID_MAX_SPIN: float = 120.0

# Длительность анимации взрыва на месте уничтоженного объекта (сек)
EXPLOSION_DURATION: float = 0.45

# Прямоугольник заставки по центру экрана: (left, top, width, height)
SPLASH_WIDTH: int = 320
SPLASH_HEIGHT: int = 140
SPLASH_RECT: tuple[int, int, int, int] = (
    (SCREEN_WIDTH - SPLASH_WIDTH) // 2,
    (SCREEN_HEIGHT - SPLASH_HEIGHT) // 2,
    SPLASH_WIDTH,
    SPLASH_HEIGHT,
)
