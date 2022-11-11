from __future__ import annotations

import pkgutil
from operator import attrgetter
from typing import Iterable

from rich.console import RenderableType, Console, ConsoleOptions
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.css.styles import RenderStyles
from textual.geometry import Size
from textual.widget import Widget
from textual.widgets import Input


class SearchCompletionRender:
    def __init__(self, filter: str, matches: Iterable[pkgutil.ModuleInfo], highlight_index: int, component_styles: dict[str, RenderStyles]) -> None:
        self.filter = filter
        self.matches = matches
        self.highlight_index = highlight_index
        self.component_styles = component_styles
        self._highlight_item_style = self.component_styles.get("search-completion--selected-item").rich_style

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        matches = []
        for match in self.matches:
            match = Text(f"{match.name:<{console.width}}", style="italic" if match.ispkg else "")
            matches.append(match)

        sorted_matches = sorted(matches, key=lambda string: not string.plain.startswith(self.filter))
        for index, match in enumerate(sorted_matches):
            if self.highlight_index == index:
                match.stylize(self._highlight_item_style)
            match.highlight_regex(self.filter, style="black on #4EBF71")

        return Text("\n").join(sorted_matches)


class SearchCompletion(Widget):

    COMPONENT_CLASSES = {
        "search-completion--selected-item",
    }

    def __init__(
        self,
        modules: Iterable[pkgutil.ModuleInfo],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.modules = sorted(modules, key=attrgetter("name"))

    @property
    def highlight_index(self) -> int:
        return self._highlight_index

    @highlight_index.setter
    def highlight_index(self, value: int) -> None:
        self._highlight_index = value % max(len(self.matches), 1)
        self.refresh()

    @property
    def search_value(self) -> str:
        return self._search_value

    @search_value.setter
    def search_value(self, value: str):
        self._search_value = value
        self.matches = [module for module in self.modules if value in module.name]
        self.parent.display = len(value) > 1 and len(self.matches) > 0
        self.refresh(layout=True)

    def on_mount(self, event: events.Mount) -> None:
        self._highlight_index = 0
        self._search_value = ""
        self.matches = [module for module in self.modules]

    def get_content_width(self, container: Size, viewport: Size) -> int:
        if not self.matches:
            return 0
        width = len(max(self.matches, key=len))
        return width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return len(self.matches)

    def render(self) -> RenderableType:
        return SearchCompletionRender(
            filter=self.search_value,
            matches=self.matches,
            highlight_index=self.highlight_index,
            component_styles=self._component_styles,
        )


class SearchBar(Input):
    def compose(self) -> ComposeResult:
        yield Input(
            value="",
            placeholder="Start typing to search...",
            id="search-input",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        value = event.value
        completion = self.app.query_one(SearchCompletion)
        completion_parent = self.app.query_one("#search-completion-container")
        input = self.query_one("#search-input", Input)
        top, right, bottom, left = completion_parent.styles.margin
        completion_parent.styles.margin = (
            top,
            right,
            bottom,
            input.cursor_position + 3
        )
        completion.search_value = value
        # Trigger the property setter to ensure validation re-runs.
        completion.highlight_index = completion.highlight_index

    def on_key(self, event: events.Key) -> None:
        completion = self.app.query_one(SearchCompletion)
        if event.key == "down":
            completion.highlight_index += 1
        elif event.key == "up":
            completion.highlight_index -= 1


