# NiceGUI

<img src="https://raw.githubusercontent.com/zauberzeug/nicegui/main/sceenshots/ui-elements.png" width="300" align="right">

NiceGUI is an easy-to-use, Python-based UI framework, which renders to the web browser.
You can create buttons, dialogs, markdown, 3D scenes, plots and much more.

It was designed to be used for micro web apps, dashboards, robotics projects, smart home solutions and similar use cases.
It is also helpful for development, for example when tweaking/configuring a machine learning algorithm or tuning motor controllers.

## Features

- browser-based graphical user interface
- shared state between multiple browser windows
- implicit reload on code change
- standard GUI elements like label, button, checkbox, switch, slider, input, file upload, ...
- simple grouping with rows, columns, cards and dialogs
- general-purpose HTML and markdown elements
- powerful high-level elements to
  - plot graphs and charts,
  - render 3D scenes,
  - get steering events via virtual joysticks
  - annotate images
- built-in timer to refresh data in intervals (even every 10 ms)
- straight-forward data binding to write even less code
- notifications, dialogs and menus to provide state of the art user interaction
- ability to add custom routes and data responses
- capture keyboard input for global shortcuts etc
- customize look by defining primary, secondary and accent colors

## Installation

```bash
python3 -m pip install nicegui
```

## Usage

Write your nice GUI in a file `main.py`:

```python
from nicegui import ui

ui.label('Hello NiceGUI!')
ui.button('BUTTON', on_click=lambda: print('button was pressed', flush=True))

ui.run()
```

Launch it with:

```bash
python3 main.py
```

The GUI is now available through http://localhost:8080/ in your browser.
Note: The script will automatically reload the page when you modify the code.

Full documentation can be found at [https://nicegui.io](https://nicegui.io).

## Configuration

You can call `ui.run()` with optional arguments for some high-level configuration:

- `host` (default: `'0.0.0.0'`)
- `port` (default: `8080`)
- `title` (default: `'NiceGUI'`)
- `favicon` (default: `'favicon.ico'`)
- `dark`: whether to use Quasar's dark mode (default: `False`, use `None` for "auto" mode)
- `reload`: automatically reload the ui on file changes (default: `True`)
- `show`: automatically open the ui in a browser tab (default: `True`)
- `on_connect`: default function or coroutine which is called for each new client connection; the optional `request` argument provides session infos
- `uvicorn_logging_level`: logging level for uvicorn server (default: `'warning'`)
- `main_page_classes`: configure Quasar classes of main page (default: `q-ma-md column items-start`)
- `interactive`: used internally when run in interactive Python shell (default: `False`)

## Docker

You can use our [multi-arch docker image](https://hub.docker.com/repository/docker/zauberzeug/nicegui) for pain-free installation:

```bash
docker run --rm -p 8888:8080 -v $(pwd):/app/ -it zauberzeug/nicegui:latest
```

This will start the server at http://localhost:8888 with the code from your current directory.
The file containing your `app.run(port=8080, ...)` command must be named `main.py`.
Code modification triggers an automatic reload.

## Why?

We like [Streamlit](https://streamlit.io/) but find it does [too much magic when it comes to state handling](https://github.com/zauberzeug/nicegui/issues/1#issuecomment-847413651).
In search for an alternative nice library to write simple graphical user interfaces in Python we discovered [justpy](https://justpy.io/).
While too "low-level HTML" for our daily usage it provides a great basis for "NiceGUI".

## API

The API reference is hosted at [https://nicegui.io](https://nicegui.io) and is [implemented with NiceGUI itself](https://github.com/zauberzeug/nicegui/blob/main/main.py).
You may also have a look at [examples.py](https://github.com/zauberzeug/nicegui/tree/main/examples.py) for more demonstrations of what you can do with NiceGUI.

## Abstraction

NiceGUI is based on [JustPy](https://justpy.io/) which is based on the ASGI framework [Starlette](https://www.starlette.io/) and the ASGI webserver [Uvicorn](https://www.uvicorn.org/).

## Deployment

To deploy your NiceGUI app, you will need to execute your `main.py` (or which ever file contains your `app.run(...)`) on your server infrastructure.
You can either install the [NiceGUI python package via pip](https://pypi.org/project/nicegui/) on the server or use our [pre-build docker image](https://hub.docker.com/r/zauberzeug/nicegui) which contains all necessary dependencies and provides a much much cleaner deployment.
For example you can use this docker run command to start the script `main.py` in the current directory on port 80:

```bash
docker run -p 80:8080 -v $(pwd)/:/app/  -d --restart always zauberzeug/nicegui:latest
```

The example assumes `main.py` uses the port 8080 in the `ui.run` command (which is the default).
The `--restart always` makes sure the container is restarted on crash of the app or reboot of the server.
Of course this can also be written in a docker compose file:

```yaml
nicegui:
  image: zauberzeug/nicegui:latest
  restart: always
  ports:
    - 80:8080
  volumes:
    - ./:/app/
```

While it's possible to provide SSL certificates directly through NiceGUI (using [JustPy config](https://justpy.io/reference/configuration/)) we suggest to use an reverse proxy like [Traefik](https://doc.traefik.io/traefik/) or [NGINX](https://www.nginx.com/).
