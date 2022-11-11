import pkgutil

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from shira._module_panel import ModulePanel
from shira._search import SearchBar, SearchCompletion


class Shira(App):
    def compose(self) -> ComposeResult:
        modules = pkgutil.iter_modules()
        yield Horizontal(
            Static(">", id="search-prompt"),
            SearchBar(id="search-input"),
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
            ModulePanel(id="module-panel"),
            id="body-container",
        )

    def on_mount(self, event: events.Mount) -> None:
        self.query_one("#search-input").focus()

    def on_search_bar_new_lookup_chain(self, event: SearchBar.NewLookupChain) -> None:
        module_panel = self.query_one("#module-panel", ModulePanel)
        self.query_one("#body-container").scroll_home(animate=False)

        new_module = event.chain[0] if event.chain else None
        module_panel.active_module = new_module


app = Shira(css_path="shira.scss")


def run():
    app.run()
