"""Точка входа в игру «Астероиды»."""

from src.app import GameApp


def main() -> None:
    """Создаёт и запускает приложение."""
    GameApp().run()


if __name__ == "__main__":
    main()
