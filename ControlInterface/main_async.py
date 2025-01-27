import asyncio
from asyncserial import Serial
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Label, Box

SEPERATOR = "\n"

private_key_pem = """
-----BEGIN RSA PRIVATE KEY-----
MIICWgIBAAKBgFs44W15Opn0ruNjtl8fY6eNmQir3AsKqj2UmZ7ShLegwob3oN1l
sn0keL401eOzjv2t7ObD/stszZao4Ugmccb83ITjEmfvHgH5rixn4+WT8sa3KW26
5IrnlfHjVRpGxRqGISf9ClyiK01acc+2EbUHqXyP+JYQwWf4+ooCYDgFAgMBAAEC
gYAiQxfwTTMkdhFl2KK70YdVfEp5RktsXkIYxQJ586njal8F4GYsIbFLbXJoRmH7
lwpi33t2JTFC6IfDSYTr23yqBJ/6DKiCa4ZsSQPd06iqz2aDHc4Bq7D2ZQMdkOMK
vpCHpTUgKW1sHYLzqzGMURMHkqBvGA39qZ3TbdBZmZuk9QJBAJ2WoSiis3FA8YUm
digwYxNepdyxXQu5f6DQm9HItMKK/BqmnL8x46nJbVZGednxN02mlzyDjG7lipUv
4LfQoHMCQQCUMGf9rZB8ZhP3RNx+wz2HFfVl8b38PLaJQ6E4WFj6Xrmnx/11+B1V
yRWbWAJZueBa3DMf4cOMtdIOsH18d/+nAkBDEhoTRnQjDqX8qqr9XeK9GrpzHJXi
aJf2ZPL8rXSpnCfCXAk4os4ntFAxuRshdDW6ed3CZqa9iDqcVl1JPqUbAkAkyfen
JMWv/G+MfY338mR9+teXXXJ7Al+WqDGIGXbNgWK54o5sERLHT0qL7Ed5Gwo1xGD0
00mGz0S83NfqZKgVAkA1FRhnKSKeTIApLSF0czX+CkO5b94wvB+UEj0BBLgCZOjr
FtM5YV3W2Q/dvCxcRie65sHIil4B7E4D7pzKf1aK
-----END RSA PRIVATE KEY-----
"""
public_key_pem = """
-----BEGIN PUBLIC KEY-----
MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgFs44W15Opn0ruNjtl8fY6eNmQir
3AsKqj2UmZ7ShLegwob3oN1lsn0keL401eOzjv2t7ObD/stszZao4Ugmccb83ITj
EmfvHgH5rixn4+WT8sa3KW265IrnlfHjVRpGxRqGISf9ClyiK01acc+2EbUHqXyP
+JYQwWf4+ooCYDgFAgMBAAE=
-----END PUBLIC KEY-----
"""


def remove_last_n_chars(input_str: str, n: int) -> str:
    """Remove the last n characters from the input string."""
    if n <= 0:
        return input_str
    return input_str[:-n] if n < len(input_str) else ""


def base64_decode(base64_message: str) -> bytes:
    """Decode a base64 encoded message."""
    try:
        decoded_bytes = base64.b64decode(base64_message)
        return decoded_bytes
    except Exception as e:
        print(f"[!] Error decoding base64 message: {e}")
        return None


def base64_encode(message: str) -> str:
    """Encode a message to base64."""
    try:
        message_bytes = message.encode("utf-8")
        base64_bytes = base64.b64encode(message_bytes)
        return base64_bytes
    except Exception as e:
        print(f"[!] Error encoding message to base64: {e}")
        return None


def parse_private_key(private_key_pem: str):
    try:
        return serialization.load_pem_private_key(
            private_key_pem.encode(), password=None
        )
    except Exception as e:
        print(f"[!] Error loading private key: {e}")
        return None


def parse_public_key(public_key_pem: str):
    try:
        return serialization.load_pem_public_key(public_key_pem.encode())
    except Exception as e:
        print(f"[!] Error loading public key: {e}")
        return None


def encrypt_message(message: str, public_key_pem: str) -> bytes | None:
    """Encrypt a message using the provided public key."""
    public_key = parse_public_key(public_key_pem)
    if public_key is None:
        return None
    try:
        encrypted_message = public_key.encrypt(
            message.encode("utf-8"),
            padding.PKCS1v15(),  # PKCS#1 v1.5 padding
        )
        return encrypted_message
    except Exception as e:
        print(f"[!] Error encrypting message: {e}")
        return None


def decrypt_message(encrypted_message: bytes, private_key_pem: str) -> str | None:
    """Decrypt a message using the provided private key."""
    private_key = parse_private_key(private_key_pem)
    if private_key is None:
        return None
    try:
        decrypted_message = private_key.decrypt(
            encrypted_message,
            padding.PKCS1v15(),  # PKCS#1 v1.5 padding
        )
        return decrypted_message.decode("utf-8")
    except Exception as e:
        print(f"[!] Error decrypting message: {e}")
        return None

async def send_message(serial_connection: Serial, message: str, sep: str = SEPERATOR):
    print(">>> Sending Encrypted Message:\n--------------{ Clear Message }\n" + message)
    result = encrypt_message(message, public_key_pem)
    result = base64.b64encode(result).decode("utf-8")
    print("--------------{ Encrypted Base64 Message }\n" + result + "\n--------------|END|\n")
    await serial_connection.write((result + sep).encode("utf-8"))

def on_receive_message(b64_message: str):
    print(
        "<<< Receiving Encrypted Message:\n--------------{ Encrypted Base64 Message }\n"
        + b64_message,
        flush=True,
    )

    encrypted_message_bytes = base64_decode(b64_message)
    if encrypted_message_bytes is None:
        return

    decrypted_message = decrypt_message(encrypted_message_bytes, private_key_pem)

    if decrypted_message is None:
        print("[!] Failed to decrypt message.")
        return
    print(
        "--------------{ Clear Message }\n"
        + decrypted_message
        + "\n--------------|END|\n",
        flush=True,
    )


async def listen_bluetooth_routine(serial_connection: Serial, raw_input_queue: asyncio.Queue):
    """Task to read from the serial connection."""
    # await serial_connection.read()  # Drop any previously received data
    try:
        while True:
            received_bytes = await serial_connection.read()  # Read a line
            received_str = received_bytes.decode("utf-8", errors="ignore")
            raw_input_queue.put_nowait(received_str)
            # print("[+] Serial read: {}".format(received_str))
            await asyncio.sleep(0.001)  # Adjust sleep if needed
    except asyncio.CancelledError:
        print("[!] Serial reader task cancelled. Exiting...")
        raise  # Re-raise to allow proper cleanup


async def listen_keyboard_routine(serial_connection: Serial, sep: str = SEPERATOR):
    async def show_dialog():
        result = await input_dialog(
            title="Input Dialog",
            text="You pressed Ctrl+E! Enter some text:",
        ).run_async()
        if result:
            asyncio.create_task(send_message(serial_connection, result))
        else:
            print("Dialog canceled.")

    key_bindings = KeyBindings()

    # Define Ctrl+E binding to open a dialog
    @key_bindings.add("c-e")
    def _(event):
        asyncio.create_task(show_dialog())
    @key_bindings.add("c-t")
    def _(event):
        asyncio.create_task(send_message(serial_connection, "led toggle"))
    @key_bindings.add("c-d")
    def _(event):
        asyncio.create_task(send_message(serial_connection, "dice roll"))
    @key_bindings.add("c-c")
    def _(event):
        raise KeyboardInterrupt

    # Create an application to listen for key bindings
    app = Application(
        layout=Layout(Box(Label("Listening for Ctrl+E..."))),
        key_bindings=key_bindings,
        full_screen=False,
    )

    await app.run_async()


# Function to show a dialog using prompt_toolkit


async def read_until_seperator_routine(
    serial_connection: Serial, raw_input_queue: asyncio.Queue, sep: str = SEPERATOR
):
    """Process input from the serial reader."""
    try:
        inp = ""
        while True:
            tmp = await raw_input_queue.get()
            for c in tmp:
                inp += c
                if inp.endswith(sep):
                    # TODO: send the input to the received messages queue
                    inp = remove_last_n_chars(inp, len(sep))
                    # todo: remove this later , only for testing
                    # await serial_connection.write(
                    #     f"{inp}{sep}".encode("utf-8")
                    # )
                    on_receive_message(inp)
                    inp = ""

    except asyncio.QueueEmpty:
        pass  # Ignore empty queue errors
    except asyncio.CancelledError:
        print("[!] Input processor task cancelled. Exiting...")
        raise  # Re-raise to allow proper cleanup


async def main(COM_port="COM4"):
    """Main coroutine to manage the event loop and serial connection."""
    loop = asyncio.get_running_loop()
    bt_received_queue = asyncio.Queue()
    listener_task, handler_task, console_task = None, None, None
    try:
        # Replace '/dev/ttyACM0' with the appropriate serial port for your system
        serial_connection = Serial(loop, COM_port, baudrate=9600)
        print("[+] Serial connection established.")

        # Start the reader task
        listener_task = asyncio.create_task(
            listen_bluetooth_routine(serial_connection, bt_received_queue)
        )

        handler_task = asyncio.create_task(
            read_until_seperator_routine(
                serial_connection, bt_received_queue, SEPERATOR
            )
        )
        console_task = asyncio.create_task(listen_keyboard_routine(serial_connection))
        # Run until interrupted
        await asyncio.sleep(float("inf"))
    except KeyboardInterrupt:
        print("\n[!] KeyboardInterrupt detected. Cleaning up...")
        listener_task.cancel()  # Cancel the reader task
        handler_task.cancel()
        console_task.cancel()
        await listener_task  # Wait for it to finish
        await handler_task
    except Exception as e:
        print(f"[!] An error occurred: {e}")
    finally:
        if serial_connection.is_open:
            print("[+] Closing serial connection...")
            await serial_connection.close()  # Close the serial connection
            print("[+] Serial connection closed. Exiting.")

        print("[+] Cleaning up...")
        if listener_task is not None:
            listener_task.cancel()  # Cancel the reader task
            await listener_task  # Wait for it to finish
        if handler_task is not None:
            handler_task.cancel()
            await handler_task
        if console_task is not None:
            console_task.cancel()
            await console_task


if __name__ == "__main__":
    try:
        asyncio.run(main("COM5"))
    except KeyboardInterrupt:
        print("\n[!] Program interrupted by user.")
