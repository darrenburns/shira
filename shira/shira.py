from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Input
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem

from shira._object_panel import ObjectPanel


def get_candidates(input_value: str, cursor_position: int) -> list[DropdownItem]:
    return [
        DropdownItem(main="A"),
        DropdownItem(main="B"),
        DropdownItem(main="C"),
        DropdownItem(main="D"),
    ]


class Shira(App):
    CSS_PATH = Path(__file__).parent / "shira.scss"

    def __init__(self, initial_object: object | None = None):
        self._initial_object = initial_object
        super().__init__()

    def compose(self) -> ComposeResult:
        yield AutoComplete(
            Input(placeholder="Type to search..."),
            dropdown=Dropdown(
                items=get_candidates,
            ),
        )
        yield ObjectPanel()


def shira(initial_object: object | None = None) -> None:
    shira_app = Shira(initial_object=initial_object)
    shira_app.run()


app = Shira()


def run():
    app.run()


if __name__ == "__main__":
    thing = Widget()
    shira(thing)
