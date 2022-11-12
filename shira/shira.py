import importlib
import inspect
import pkgutil

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from shira._object_panel import ObjectPanel
from shira._search import SearchBar, SearchCompletion, CompletionCandidate

NOT_FOUND = "poi12zn@$][]daza"


class Shira(App):
    def compose(self) -> ComposeResult:
        self.modules = {module.name: module for module in pkgutil.iter_modules()}
        self.original_candidates = [
            CompletionCandidate(
                primary=module.name,
                secondary="pkg" if module.ispkg else "mod",
                original_object=module,
            )
            for module in self.modules.values()
        ]
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
        completion = self.app.query_one(SearchCompletion)

        value = event.value
        if len(value) < 2:
            completion.parent.display = False
            return

        cursor_position = event.cursor_position

        # Fill up the list of candidates
        # How do we determine the candidates?
        # Active object should be the right-most resolvable part in the string
        # The left-most part should look in the self.modules to kick off the search.
        # TODO: Cache active objects, don't naively reset it each time if it's the
        #  same as it was before
        parts = [part for part in value.split(".")]

        object_panel = self.query_one("#object-panel", ObjectPanel)
        search_part = ""
        if len(parts) == 0:
            # If we're empty, then there should be no candidates
            completion.update_candidates([])
        elif len(parts) == 1:
            # If there's only one part, then we're searching for module_name in self.modules
            module_name = parts[0]

            # Trim down the candidate list to those containing the query string
            candidates = []
            for candidate in self.original_candidates:
                if module_name in candidate.primary:
                    candidates.append(candidate)
                if module_name == candidate.primary:
                    object_panel.active_object = candidate.original_object

            # Update the dropdown list with the new candidates
            completion.update_candidates(candidates)
            # Tell the dropdown list about the part to use for highlighting matching candidates
            # Since there's only 1 part, we don't need to do anything tricky here
            search_part = module_name
        else:
            # We have multiple parts now, so finding our list of candidates is more complex
            # We'll look through the parts to get to the rightmost valid part BEFORE the cursor position.
            module_name = parts[0]
            other_parts = parts[1:]

            search_input = self.query_one("#search-input", SearchBar)
            cursor_position = search_input.cursor_position

            # Now we need to get into a scenario where we have an object that we wish to search,
            # and a search string to apply to it
            object_to_search = self.modules.get(module_name)

            if object_to_search is None:
                completion.update_candidates([])
            else:
                # TODO: We should update this loop to only go up to the cursor position
                search_part = ""
                for part in other_parts:
                    if part == "":
                        break

                    if isinstance(object_to_search, pkgutil.ModuleInfo):
                        object_to_search = importlib.import_module(
                            object_to_search.name
                        )

                    # Look for this part on the current object to search
                    object_dict = getattr(object_to_search, "__dict__", None)
                    if object_dict is None:
                        completion.update_candidates([])
                        break

                    obj = object_dict.get(part, NOT_FOUND)
                    if obj == NOT_FOUND:
                        search_part = part
                        break
                    else:
                        object_to_search = obj

                if object_to_search is not None:
                    if isinstance(object_to_search, pkgutil.ModuleInfo):
                        object_to_search = importlib.import_module(
                            object_to_search.name
                        )

                    if hasattr(object_to_search, "__dict__"):
                        new_candidates = []
                        for name, obj in object_to_search.__dict__.items():
                            print(obj, getattr(obj, "__package__", None))
                            if name.startswith("__") and name.endswith("__"):
                                continue

                            is_module = inspect.ismodule(obj)
                            if is_module and getattr(
                                obj, "__package__", "-x-"
                            ) == getattr(object_to_search, "__package__", "-y-"):
                                new_candidates.append(
                                    CompletionCandidate(
                                        name, "mod", original_object=obj
                                    )
                                )
                            elif not is_module:
                                obj_module = inspect.getmodule(obj)
                                if inspect.ismodule(object_to_search):
                                    include = obj_module is object_to_search
                                else:
                                    include = obj_module is inspect.getmodule(
                                        object_to_search
                                    )

                                if include:
                                    new_candidates.append(
                                        CompletionCandidate(
                                            name, None, original_object=obj
                                        )
                                    )

                            # If it's a module, include if it has same __package__
                            # If it's not a module, include if in same module

                        completion.update_candidates(new_candidates)

                object_panel.active_object = object_to_search

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
        completion.filter = search_part
        completion.highlight_index = completion.highlight_index


app = Shira(css_path="shira.scss")


def run():
    app.run()
