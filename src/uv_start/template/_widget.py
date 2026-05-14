"""Hello-world napari widget built with magicgui."""

from magicgui import magic_factory


@magic_factory(call_button="Say hello")
def hello_widget(name: str = "world") -> str:
    message = f"Hello, {name}!"
    print(message)
    return message
