"""Bounded, shell-free child I/O for trusted local tools and pinned SSH."""
import os
import selectors
import subprocess
import time


class ProcessFailed(RuntimeError):
    pass


def run(argv, *, payload=b'', timeout=10, output_limit=4096, pass_fds=()):
    if not 0 < timeout <= 60 or type(payload) is not bytes or len(payload) > 8192:
        raise ValueError('invalid process bounds')
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, pass_fds=pass_fds, close_fds=True)
    deadline = time.monotonic() + timeout
    result = bytearray()
    offset = 0
    try:
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            if payload:
                os.set_blocking(process.stdin.fileno(), False)
                selector.register(process.stdin, selectors.EVENT_WRITE)
            else:
                process.stdin.close()
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProcessFailed('process-timeout')
                for key, _ in selector.select(remaining):
                    if key.fileobj is process.stdin:
                        try:
                            offset += os.write(process.stdin.fileno(), payload[offset:offset+4096])
                        except BrokenPipeError:
                            raise ProcessFailed('process-input') from None
                        if offset == len(payload):
                            selector.unregister(process.stdin)
                            process.stdin.close()
                    else:
                        chunk = os.read(process.stdout.fileno(), min(4096, output_limit + 1 - len(result)))
                        if not chunk:
                            selector.unregister(process.stdout)
                            continue
                        result.extend(chunk)
                        if len(result) > output_limit:
                            raise ProcessFailed('process-output')
            remaining = deadline - time.monotonic()
            if remaining <= 0 or process.wait(timeout=remaining) != 0:
                raise ProcessFailed('process-exit')
            return bytes(result)
    except subprocess.TimeoutExpired:
        raise ProcessFailed('process-timeout') from None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdin.close()
        process.stdout.close()
