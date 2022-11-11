import importlib

from rich._inspect import Inspect

from rich.console import RenderableType
from textual import events
from textual.widget import Widget


class ModulePanel(Widget, can_focus=True):

    def on_mount(self, event: events.Mount) -> None:
        self.active_module = None

    @property
    def active_module(self):
        return self._active_module

    @active_module.setter
    def active_module(self, value):
        self._active_module = value
        self.refresh(layout=True)

    def render(self) -> RenderableType:
        active_module = self.active_module
        if active_module is None:
            return "No selection"
        active_module = importlib.import_module(active_module.name)
        return Inspect(active_module)
