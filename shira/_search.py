from __future__ import annotations

import pkgutil
from dataclasses import dataclass
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


@dataclass
class CompletionCandidate:
    primary: str
    secondary: str
    original_object: pkgutil.ModuleInfo | None


class SearchCompletionRender:
    def __init__(self, filter: str, matches: Iterable[CompletionCandidate],
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
                f"{match.primary:<{options.max_width - 3}}[dim]{match.secondary}")
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
        candidates: Iterable[CompletionCandidate],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.candidates = []
        self.update_candidates(candidates)

    def update_candidates(self, new_candidates: Iterable[CompletionCandidate]) -> None:
        self.candidates = sorted(new_candidates, key=attrgetter("primary"))

    @property
    def highlighted_candidate(self):
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
    def filter(self) -> str:
        return self._filter

    @filter.setter
    def filter(self, value: str):
        self._filter = value

        right_dot_index = value.rfind(".")
        if right_dot_index == -1:
            search_value = value
        else:
            search_value = value[right_dot_index + 1:]

        print("-----")
        print(search_value)
        print([candidate.primary for candidate in self.candidates])
        print("-----")

        new_matches = []
        for candidate in self.candidates:
            if search_value in candidate.primary:
                new_matches.append(candidate)

        self.matches = sorted(new_matches,
                              key=lambda candidate: candidate.primary.startswith(
                                  search_value),
                              reverse=True)
        self.parent.display = len(self.matches) > 0
        self.refresh()

    def on_mount(self, event: events.Mount) -> None:
        self._highlight_index = 0
        self._filter = ""
        self.matches = sorted([candidate for candidate in self.candidates],
                              key=attrgetter("primary"))

    def get_content_width(self, container: Size, viewport: Size) -> int:
        if not self.matches:
            return 0
        width = len(max([match.primary for match in self.matches], key=len))
        return width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return len(self.matches)

    def render(self) -> RenderableType:
        return SearchCompletionRender(
            filter=self.filter,
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
        self.emit_no_wait(SearchBar.Updated(self, value, self.cursor_position))

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
                candidate = completion.highlighted_candidate
                right_dot = self.value.rfind(".")
                if right_dot == -1:
                    self.value = candidate.primary + "."
                else:
                    self.value = f"{self.value[:right_dot]}.{candidate.primary}."
                self.cursor_position = len(self.value)
                event.stop()

        # TODO: More sensible scrolling
        x, y, width, height = completion.region
        target_region = Region(x, completion.highlight_index, width, height)
        completion_parent.scroll_to_region(target_region, animate=False)

    class Updated(Message, bubble=True):
        def __init__(self, sender: SearchBar,
                     value: str, cursor_position: int) -> None:
            super().__init__(sender)
            self.value = value
            self.cursor_position = cursor_position
