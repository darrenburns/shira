from __future__ import annotations

import pkgutil
from operator import attrgetter
from typing import Iterable

from rich.console import RenderableType, Console, ConsoleOptions
from rich.text import Text
from textual import events
from textual.css.styles import RenderStyles
from textual.geometry import Size, Region
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input


class SearchCompletionRender:
    def __init__(self, filter: str, matches: Iterable[pkgutil.ModuleInfo],
                 highlight_index: int,
                 component_styles: dict[str, RenderStyles]) -> None:
        self.filter = filter
        self.matches = matches
        self.highlight_index = highlight_index
        self.component_styles = component_styles
        self._highlight_item_style = self.component_styles.get(
            "search-completion--selected-item").rich_style

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        matches = []
        for index, match in enumerate(self.matches):
            match = Text.from_markup(
                f"{match.name:<{options.max_width - 3}}[dim]{'pkg' if match.ispkg else 'mod'}")
            matches.append(match)
            if self.highlight_index == index:
                match.stylize(self._highlight_item_style)
            match.highlight_regex(self.filter, style="black on #4EBF71")

        return Text("\n").join(matches)


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
    def highlighted_module(self):
        if not self.matches:
            return 0
        return self.matches[self.highlight_index]

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
        new_matches = [module for module in self.modules if value in module.name]
        self.matches = sorted(new_matches,
                              key=lambda module: module.name.startswith(value),
                              reverse=True)
        self.parent.display = len(value) > 1 and len(self.matches) > 0
        self.refresh()

    def on_mount(self, event: events.Mount) -> None:
        self._highlight_index = 0
        self._search_value = ""
        self.matches = sorted([module for module in self.modules],
                              key=attrgetter("name"))

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

    def __init__(self, name: str | None = None,
                 id: str | None = None,
                 classes: str | None = None):
        super().__init__(
            placeholder="Start typing to search...",
            name=name,
            id=id,
            classes=classes,
        )

    def watch_value(self, value: str) -> None:
        completion = self.app.query_one(SearchCompletion)
        completion_parent = self.app.query_one("#search-completion-container")
        top, right, bottom, left = completion_parent.styles.margin
        completion_parent.styles.margin = (
            top,
            right,
            bottom,
            self.cursor_position + 3
        )
        completion.search_value = value
        # Trigger the property setter to ensure validation re-runs.
        completion.highlight_index = completion.highlight_index

    def on_key(self, event: events.Key) -> None:
        completion = self.app.query_one(SearchCompletion)
        completion_parent = self.app.query_one("#search-completion-container")

        # TODO: Scroll the completion container appropriately
        if event.key == "down":
            completion.highlight_index += 1
            event.stop()
        elif event.key == "up":
            completion.highlight_index -= 1
            event.stop()
        elif event.key == "tab":
            if completion_parent.display:
                # The dropdown is visible, fill in the completion string
                module = completion.highlighted_module
                value = module.name + " "
                self.value = value
                self.cursor_position = len(value)
                completion.highlight_index = completion.highlight_index
                completion_parent.display = False

                self.emit_no_wait(self.NewLookupChain(self, [module]))

                event.stop()

        # TODO: More sensible scrolling
        x, y, width, height = completion.region
        target_region = Region(x, completion.highlight_index, width, height)
        completion_parent.scroll_to_region(target_region, animate=False)

    class NewLookupChain(Message, bubble=True):
        def __init__(self, sender: SearchBar,
                     chain: list[str | pkgutil.ModuleInfo]) -> None:
            super().__init__(sender)
            self.chain = chain
