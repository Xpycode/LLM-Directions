"""Fixed disposable peers for recovery_observer.py; no native or input APIs."""
import json
import os
import sys
import threading
import time


def emit(stream, event, **fields):
    stream.write(json.dumps(dict(event=event, ns=time.monotonic_ns(), **fields)) + "\n")
    stream.flush()


def main():
    role, fault = sys.argv[1:3]
    if role == "supervisor":
        # This process is the sole owner of the worker command writer.
        with os.fdopen(int(sys.argv[3]), "w") as worker:
            emit(sys.stdout, "ready")
            for line in sys.stdin:
                op = json.loads(line)["op"]
                if op == "pair":
                    for tag in (1, 2):
                        worker.write(json.dumps(dict(tag=tag)) + "\n")
                        worker.flush()
                elif op == "crash":
                    emit(sys.stdout, "crashing")
                    os._exit(17)
    elif role == "worker":
        with os.fdopen(int(sys.argv[3]), "w") as recorder:
            emit(sys.stdout, "ready")
            for line in sys.stdin:
                tag = json.loads(line)["tag"]
                emit(recorder, "receipt", tag=tag)
                emit(sys.stdout, "posted", tag=tag)
            emit(sys.stdout, "commandEOF")
            if fault == "hung-worker":
                time.sleep(60)  # Observer must bound cleanup of this owned peer.
            if fault == "late-receipt":
                emit(recorder, "receipt", tag=3)
            emit(sys.stdout, "stopped", heldKeysEmpty=True)
            emit(sys.stdout, "observationComplete")
    elif role == "recorder":
        # Separate data pipe ends with the worker; observer control remains open.
        # Joining this reader before the fence gives the acknowledgement an
        # actual stream boundary, not merely a delay or a fresh final sample.
        def read_events():
            with os.fdopen(int(sys.argv[3])) as events:
                for line in events:
                    row = json.loads(line)
                    emit(sys.stdout, row["event"], tag=row["tag"])
            emit(sys.stdout, "sourceEOF")

        reader = threading.Thread(target=read_events, daemon=True)
        emit(sys.stdout, "ready")
        reader.start()
        for line in sys.stdin:
            if json.loads(line)["op"] == "observeEnd":
                reader.join(timeout=2)
                if not reader.is_alive() and fault != "missing-fence":
                    emit(sys.stdout, "observationComplete")
        reader.join(timeout=2)
        if reader.is_alive():
            return 2
        if fault == "recorder-exit-failure":
            return 7
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
