from abc import ABC, abstractmethod

from hipster.html_generator import HTMLGenerator


class Task(ABC):
    """Base class for all tasks.

    Args:
        name (str): The name of the task.
        root_path (str): The root path for the task. Defaults to "".
        title (str): The title of the task. Defaults to "".
        skip (bool): Whether to skip the task. Defaults to False.
    """

    def __init__(
        self,
        name,
        root_path: str = "",
        title: str = "",
        skip: bool = False,
    ) -> None:
        super().__init__()
        self.name = name
        self.root_path = root_path
        self.title = title
        self.skip = skip

    @abstractmethod
    def execute(self) -> None:
        """Execute the task."""

    @abstractmethod
    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the task with the HTML generator.
        Args:
            html_generator (HTMLGenerator): The HTML generator instance.
        """
