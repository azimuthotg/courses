import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from waitress import serve


BASE_DIR = Path(__file__).resolve().parent.parent


def _configure_encoding():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')


def main():
    _configure_encoding()
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    load_dotenv(BASE_DIR / '.env')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    from config.wsgi import application

    host = os.getenv('WAITRESS_HOST', '127.0.0.1')
    port = int(os.getenv('WAITRESS_PORT', '8002'))
    threads = int(os.getenv('WAITRESS_THREADS', '8'))

    print(f'Starting Micro-LMS on http://{host}:{port}')
    serve(application, host=host, port=port, threads=threads)


if __name__ == '__main__':
    main()
