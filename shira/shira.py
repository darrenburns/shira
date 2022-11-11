import importlib
import inspect
import pkgutil
from types import ModuleType

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from shira._object_panel import ObjectPanel
from shira._search import SearchBar, SearchCompletion, CompletionCandidate


class Shira(App):
    def compose(self) -> ComposeResult:
        self.modules = {module.name: module for module in pkgutil.iter_modules()}
        self.original_candidates = [CompletionCandidate(
            primary=module.name,
            secondary='pkg' if module.ispkg else 'mod',
            original_object=module,
        )
            for module in self.modules.values()]
        yield Horizontal(
            Static(">", id="search-prompt"),
            SearchBar(id="search-input"),
            id="search-bar-container",
        )
        yield Container(
            SearchCompletion(
                candidates=self.original_candidates,
                id="search-completion",
            ),
            id="search-completion-container",
        )
        yield Container(
            ObjectPanel(id="object-panel"),
            id="body-container",
        )

    def on_mount(self, event: events.Mount) -> None:
        self.query_one("#search-input").focus()

    def on_search_bar_updated(self, event: SearchBar.Updated) -> None:

        print("SEARCH BAR UPDATED")
        completion = self.app.query_one(SearchCompletion)

        value = event.value
        cursor_position = event.cursor_position

        # Fill up the list of candidates
        # How do we determine the candidates?
        # Active object should be the right-most resolvable part in the string
        # The left-most part should look in the self.modules to kick off the search.
        # TODO: Cache active objects, don't naively reset it each time if it's the
        #  same as it was before
        parts = [part for part in value.split(".") if part != ""]

        if len(parts) == 1:
            # If there's only one part, then we're searching for module_name in self.modules
            module_name = parts[0]
            # Trim down the candidate list to those containing the query string
            # candidates = [candidate for candidate in self.original_candidates if module_name in candidate]
            candidates = []
            for candidate in self.original_candidates:
                if module_name in candidate.primary:
                    candidates.append(candidate)
                if module_name == candidate.primary:
                    object_panel = self.query_one("#object-panel", ObjectPanel)
                    object_panel.active_object = candidate.original_object

            # Update the dropdown list with the new candidates
            completion.update_candidates(candidates)
            # Tell the dropdown list about the part to use for highlighting matching candidates
            # Since there's only 1 part, we don't need to do anything tricky here
            completion.filter = module_name
        else:
            # We have multiple parts now, so finding our list of candidates is more complex
            # TODO
            pass

        #
        #
        # other_parts = [part for part in parts[1:] if part]
        # if not other_parts:
        #     new_active_object = root_module
        # else:
        #     # Lets look through the parts to find the rightmost available object
        #     new_active_object = None
        #     parent = parts[0]
        #     for part in other_parts:
        #         try:
        #             child = getattr(parent, part)
        #         except AttributeError:
        #             # Went as far as we can, use the child
        #             break
        #         else:
        #             parent = child
        #
        #         new_active_object = child
        #
        # new_candidates = []
        # for name, val in new_active_object.__dict__.items():
        #     if isinstance(val, ModuleType):
        #         val = importlib.import_module(val.__name__)
        #     new_candidates.append(
        #         CompletionCandidate(
        #             primary=name,
        #             secondary="bla",  # TODO: fixme
        #             original_object=val,
        #         )
        #     )
        # print(f"UPDATING CANDIDATES TO {new_candidates}")
        # completion.update_candidates(new_candidates)



        # The search bar has updated, so lets update the completion dropdown
        # First, align it with the cursor position
        completion_parent = self.app.query_one("#search-completion-container")
        top, right, bottom, left = completion_parent.styles.margin
        completion_parent.styles.margin = (
            top,
            right,
            bottom,
            cursor_position + 3,
        )
        completion.filter = value
        completion.highlight_index = completion.highlight_index


app = Shira(css_path="shira.scss")


def run():
    app.run()
