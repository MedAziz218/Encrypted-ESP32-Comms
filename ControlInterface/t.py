import asyncio
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Label, Box

# Task 1: Prints "hello <i>" every second, incrementing i
async def print_hello():
    i = 0
    while True:
        print(f"hello {i}")
        i += 1
        await asyncio.sleep(1)

# Task 2: Listens for keyboard input with Ctrl+E handling
async def listen_keyboard():
    key_bindings = KeyBindings()

    # Define Ctrl+E binding to open a dialog
    @key_bindings.add("c-e")
    def _(event):
        asyncio.create_task(show_dialog())
    @key_bindings.add("c-c")
    def _(event):
        quit()

    # Create an application to listen for key bindings
    app = Application(
        layout=Layout(Box(Label("Listening for Ctrl+E..."))),
        key_bindings=key_bindings,
        full_screen=False,
    )

    await app.run_async()

# Function to show a dialog using prompt_toolkit
async def show_dialog():
    result = await input_dialog(
        title="Input Dialog",
        text="You pressed Ctrl+E! Enter some text:",
    ).run_async()
    if result:
        print(f"You entered: {result}")
    else:
        print("Dialog canceled.")

# Main function to run tasks concurrently
async def main():
    await asyncio.gather(
        # print_hello(),
        listen_keyboard(),
    )

if __name__ == "__main__":
    asyncio.run(main())
