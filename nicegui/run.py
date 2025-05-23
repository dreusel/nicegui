import multiprocessing
import os
import socket
import sys
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Union

import __main__
import uvicorn
from starlette.routing import Route
from uvicorn.main import STARTUP_FAILURE
from uvicorn.supervisors import ChangeReload, Multiprocess

from . import globals, helpers
from . import native as native_module
from . import native_mode
from .air import Air
from .language import Language

APP_IMPORT_STRING = 'nicegui:app'


class CustomServerConfig(uvicorn.Config):
    storage_secret: Optional[str] = None
    method_queue: Optional[multiprocessing.Queue] = None
    response_queue: Optional[multiprocessing.Queue] = None


class Server(uvicorn.Server):

    def run(self, sockets: Optional[List[socket.socket]] = None) -> None:
        globals.server = self
        assert isinstance(self.config, CustomServerConfig)
        if self.config.method_queue is not None and self.config.response_queue is not None:
            native_module.method_queue = self.config.method_queue
            native_module.response_queue = self.config.response_queue
            globals.app.native.main_window = native_module.WindowProxy()

        helpers.set_storage_secret(self.config.storage_secret)
        super().run(sockets=sockets)


def run(*,
        host: Optional[str] = None,
        port: int = 8080,
        title: str = 'NiceGUI',
        viewport: str = 'width=device-width, initial-scale=1',
        favicon: Optional[Union[str, Path]] = None,
        dark: Optional[bool] = False,
        language: Language = 'en-US',
        binding_refresh_interval: float = 0.1,
        show: bool = True,
        on_air: Optional[Union[str, Literal[True]]] = None,
        native: bool = False,
        window_size: Optional[Tuple[int, int]] = None,
        fullscreen: bool = False,
        frameless: bool = False,
        reload: bool = True,
        uvicorn_logging_level: str = 'warning',
        uvicorn_reload_dirs: str = '.',
        uvicorn_reload_includes: str = '*.py',
        uvicorn_reload_excludes: str = '.*, .py[cod], .sw.*, ~*',
        tailwind: bool = True,
        prod_js: bool = True,
        endpoint_documentation: Literal['none', 'internal', 'page', 'all'] = 'none',
        storage_secret: Optional[str] = None,
        **kwargs: Any,
        ) -> None:
    '''ui.run

    You can call `ui.run()` with optional arguments:

    :param host: start server with this host (defaults to `'127.0.0.1` in native mode, otherwise `'0.0.0.0'`)
    :param port: use this port (default: `8080`)
    :param title: page title (default: `'NiceGUI'`, can be overwritten per page)
    :param viewport: page meta viewport content (default: `'width=device-width, initial-scale=1'`, can be overwritten per page)
    :param favicon: relative filepath, absolute URL to a favicon (default: `None`, NiceGUI icon will be used) or emoji (e.g. `'🚀'`, works for most browsers)
    :param dark: whether to use Quasar's dark mode (default: `False`, use `None` for "auto" mode)
    :param language: language for Quasar elements (default: `'en-US'`)
    :param binding_refresh_interval: time between binding updates (default: `0.1` seconds, bigger is more CPU friendly)
    :param show: automatically open the UI in a browser tab (default: `True`)
    :param on_air: tech preview: `allows temporary remote access <https://nicegui.io/documentation#nicegui_on_air>`_ if set to `True` (default: disabled)
    :param native: open the UI in a native window of size 800x600 (default: `False`, deactivates `show`, automatically finds an open port)
    :param window_size: open the UI in a native window with the provided size (e.g. `(1024, 786)`, default: `None`, also activates `native`)
    :param fullscreen: open the UI in a fullscreen window (default: `False`, also activates `native`)
    :param frameless: open the UI in a frameless window (default: `False`, also activates `native`)
    :param reload: automatically reload the UI on file changes (default: `True`)
    :param uvicorn_logging_level: logging level for uvicorn server (default: `'warning'`)
    :param uvicorn_reload_dirs: string with comma-separated list for directories to be monitored (default is current working directory only)
    :param uvicorn_reload_includes: string with comma-separated list of glob-patterns which trigger reload on modification (default: `'.py'`)
    :param uvicorn_reload_excludes: string with comma-separated list of glob-patterns which should be ignored for reload (default: `'.*, .py[cod], .sw.*, ~*'`)
    :param tailwind: whether to use Tailwind (experimental, default: `True`)
    :param prod_js: whether to use the production version of Vue and Quasar dependencies (default: `True`)
    :param endpoint_documentation: control what endpoints appear in the autogenerated OpenAPI docs (default: 'none', options: 'none', 'internal', 'page', 'all')
    :param storage_secret: secret key for browser-based storage (default: `None`, a value is required to enable ui.storage.individual and ui.storage.browser)
    :param kwargs: additional keyword arguments are passed to `uvicorn.run`    
    '''
    globals.ui_run_has_been_called = True
    globals.reload = reload
    globals.title = title
    globals.viewport = viewport
    globals.favicon = favicon
    globals.dark = dark
    globals.language = language
    globals.binding_refresh_interval = binding_refresh_interval
    globals.tailwind = tailwind
    globals.prod_js = prod_js
    globals.endpoint_documentation = endpoint_documentation

    for route in globals.app.routes:
        if not isinstance(route, Route):
            continue
        if route.path.startswith('/_nicegui') and hasattr(route, 'methods'):
            route.include_in_schema = endpoint_documentation in {'internal', 'all'}
        if route.path == '/' or route.path in globals.page_routes.values():
            route.include_in_schema = endpoint_documentation in {'page', 'all'}

    if on_air:
        globals.air = Air('' if on_air is True else on_air)

    if multiprocessing.current_process().name != 'MainProcess':
        return

    if reload and not hasattr(__main__, '__file__'):
        globals.log.warning('auto-reloading is only supported when running from a file')
        globals.reload = reload = False

    if fullscreen:
        native = True
    if frameless:
        native = True
    if window_size:
        native = True
    if native:
        show = False
        host = host or '127.0.0.1'
        port = native_mode.find_open_port()
        width, height = window_size or (800, 600)
        native_mode.activate(host, port, title, width, height, fullscreen, frameless)
    else:
        host = host or '0.0.0.0'

    # NOTE: We save host and port in environment variables so the subprocess started in reload mode can access them.
    os.environ['NICEGUI_HOST'] = host
    os.environ['NICEGUI_PORT'] = str(port)

    if show:
        helpers.schedule_browser(host, port)

    def split_args(args: str) -> List[str]:
        return [a.strip() for a in args.split(',')]

    # NOTE: The following lines are basically a copy of `uvicorn.run`, but keep a reference to the `server`.

    config = CustomServerConfig(
        APP_IMPORT_STRING if reload else globals.app,
        host=host,
        port=port,
        reload=reload,
        reload_includes=split_args(uvicorn_reload_includes) if reload else None,
        reload_excludes=split_args(uvicorn_reload_excludes) if reload else None,
        reload_dirs=split_args(uvicorn_reload_dirs) if reload else None,
        log_level=uvicorn_logging_level,
        **kwargs,
    )
    config.storage_secret = storage_secret
    config.method_queue = native_module.method_queue if native else None
    config.response_queue = native_module.response_queue if native else None
    globals.server = Server(config=config)

    if (reload or config.workers > 1) and not isinstance(config.app, str):
        globals.log.warning('You must pass the application as an import string to enable "reload" or "workers".')
        sys.exit(1)

    if config.should_reload:
        sock = config.bind_socket()
        ChangeReload(config, target=globals.server.run, sockets=[sock]).run()
    elif config.workers > 1:
        sock = config.bind_socket()
        Multiprocess(config, target=globals.server.run, sockets=[sock]).run()
    else:
        globals.server.run()
    if config.uds:
        os.remove(config.uds)  # pragma: py-win32

    if not globals.server.started and not config.should_reload and config.workers == 1:
        sys.exit(STARTUP_FAILURE)
