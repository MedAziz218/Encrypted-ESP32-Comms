import asyncio
from asyncserial import Serial
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

async def listener_routine(serial_connection: Serial, raw_input_queue: asyncio.Queue):
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

async def read_until_seperator_routine(
    serial_connection: Serial, raw_input_queue: asyncio.Queue, sep: str = SEPERATOR
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
                        inp = remove_last_n_chars(inp, len(sep))
                        print(inp, end="", flush=True)
                        #todo: remove this later , only for testing
                        await serial_connection.write(
                            f"{inp}{sep}".encode("utf-8")
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
            read_until_seperator_routine(serial_connection, input_queue,SEPERATOR)
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
