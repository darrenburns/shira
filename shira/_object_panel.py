import importlib
from pkgutil import ModuleInfo

from rich._inspect import Inspect

from rich.console import RenderableType
from textual import events
from textual.widget import Widget


class ObjectPanel(Widget, can_focus=True):
    def on_mount(self, event: events.Mount) -> None:
        self.active_object = None

    @property
    def active_object(self):
        return self._active_object

    @active_object.setter
    def active_object(self, value):
        self._active_object = value
        self.refresh(layout=True)

    def render(self) -> RenderableType:
        active_object = self.active_object
        if active_object is None:
            return "No selection"

        # If we've received some ModuleInfo, then import it to display full info
        if isinstance(active_object, ModuleInfo):
            active_object = importlib.import_module(active_object.name)

        return Inspect(active_object, help=True, all=False)
