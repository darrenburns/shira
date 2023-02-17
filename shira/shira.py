from __future__ import annotations

import pkgutil
from pathlib import Path

from rich.segment import Segment
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Input, Label
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem


def get_candidates(input_value: str, cursor_position: int) -> list[DropdownItem]:
    if "." not in input_value:
        return [
            DropdownItem(main=module.name)
            for module in pkgutil.iter_modules()
            if input_value in module.name
        ]

    return [
        DropdownItem(main="A"),
        DropdownItem(main="B"),
        DropdownItem(main="C"),
        DropdownItem(main="D"),
    ]


class Logo(Widget):
    def compose(self) -> ComposeResult:
        yield Label(">", id="logo")


class Crosshatch(Widget):
    COMPONENT_CLASSES = {
        "crosshatch",
    }

    def render_line(self, y: int) -> Strip:
        style = self.get_component_rich_style("crosshatch")
        segments = [
            Segment("╲" * self.region.width, style=style)
        ]
        return Strip(segments)


class Shira(App):
    CSS_PATH = Path(__file__).parent / "shira.scss"

    def __init__(self, initial_object: object | None = None):
        self._initial_object = initial_object
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Logo(),
            AutoComplete(
                Input(placeholder="Type to search...", id="search-bar"),
                dropdown=Dropdown(
                    items=get_candidates,
                    id="dropdown"
                ),
            ),
            id="search-container",
        )
        yield Crosshatch()
        # yield ObjectPanel(self._initial_object)

    def on_mount(self) -> None:
        self.query_one("#search-bar").focus(scroll_visible=False)


def shira(initial_object: object | None = None) -> None:
    shira_app = Shira(initial_object=initial_object)
    shira_app.run()


app = Shira()


def run():
    app.run()


if __name__ == "__main__":
    thing = Widget()
    shira(thing)
