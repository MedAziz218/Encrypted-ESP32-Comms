import asyncio
from asyncserial import Serial


async def listener_routine(serial_connection: Serial, raw_input_queue: asyncio.Queue):
    """Task to read from the serial connection."""
    # await serial_connection.read()  # Drop any previously received data
    try:
        while True:
            received_bytes = await serial_connection.read()  # Read a line
            received_str = received_bytes.decode("utf-8", errors="ignore")
            raw_input_queue.put_nowait(received_str)
            # print("[+] Serial read: {}".format(line_str))
            await asyncio.sleep(0.001)  # Adjust sleep if needed
    except asyncio.CancelledError:
        print("[!] Serial reader task cancelled. Exiting...")
        raise  # Re-raise to allow proper cleanup


async def read_until_seperator_routine(
    serial_connection: Serial, raw_input_queue: asyncio.Queue, sep: str = "abc"
):
    """Process input from the serial reader."""
    try:
        inp = ""
        while True:
            await asyncio.sleep(0.1)
            if raw_input_queue.empty():
                continue
            while not raw_input_queue.empty():
                tmp = raw_input_queue.get_nowait()
                for c in tmp:
                    inp += c
                    if inp.endswith(sep):
                        #TODO: send the input to the received messages queue
                        print(inp, end="", flush=True)
                        await serial_connection.write(
                            f"received <{inp}>\n".encode("utf-8")
                        )
                        inp = ""

    except asyncio.QueueEmpty:
        pass  # Ignore empty queue errors
    except asyncio.CancelledError:
        print("[!] Input processor task cancelled. Exiting...")
        raise  # Re-raise to allow proper cleanup


async def main(COM_port="COM4"):
    """Main coroutine to manage the event loop and serial connection."""
    loop = asyncio.get_running_loop()
    input_queue = asyncio.Queue()
    try:
        # Replace '/dev/ttyACM0' with the appropriate serial port for your system
        serial_connection = Serial(loop, COM_port, baudrate=9600)
        print("[+] Serial connection established.")

        # Start the reader task
        listener_task = asyncio.create_task(
            listener_routine(serial_connection, input_queue)
        )
        handler_task = asyncio.create_task(
            read_until_seperator_routine(serial_connection, input_queue)
        )
        # Run until interrupted
        await asyncio.sleep(float("inf"))
    except KeyboardInterrupt:
        print("\n[!] KeyboardInterrupt detected. Cleaning up...")
        listener_task.cancel()  # Cancel the reader task
        handler_task.cancel()
        await listener_task  # Wait for it to finish
        await handler_task
    except Exception as e:
        print(f"[!] An error occurred: {e}")
    finally:
        print("[+] Closing serial connection...")
        # await serial_connection.close()  # Close the serial connection
        print("[+] Serial connection closed. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main("COM5"))
    except KeyboardInterrupt:
        print("\n[!] Program interrupted by user.")
