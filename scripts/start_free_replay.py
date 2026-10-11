"""Independent Free hosting entrypoint: recorded replay only, never paid analysis."""
import os

from start_deployment import main as start_application


def main():
    # Fail closed even if host variables accidentally request live/static mode.
    os.environ['GAMEQA_PUBLIC_REPLAY'] = '1'
    os.environ.pop('GAMEQA_PUBLIC_STATIC', None)
    os.environ.pop('OPENROUTER_API_KEY', None)
    os.environ.pop('GEMINI_API_KEY', None)
    start_application()


if __name__ == '__main__':
    main()
