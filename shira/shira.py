import pkgutil

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Input

from shira._search import SearchBar, SearchCompletion


class Shira(App):
    def compose(self) -> ComposeResult:
        modules = pkgutil.iter_modules()
        yield Horizontal(
            Static(">", id="search-prompt"),
            SearchBar(id="search-bar"),
            id="search-bar-container",
        )
        yield Container(
            SearchCompletion(
                modules=modules,
                id="search-completion",
            ),
            id="search-completion-container",
        )
        yield Container(
            Static("Body content"),
            id="body-container",
        )

    def on_mount(self, event: events.Mount) -> None:
        self.query_one("#search-input").focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        value = event.value


app = Shira(css_path="shira.scss")


def run():
    app.run()
