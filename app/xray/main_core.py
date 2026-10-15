"""Local core lifecycle with a main-only overlay, bounded apply and rollback.

The base configuration remains reusable by Nodes. Only the singleton local
core is this subclass; remote and relay processes never use its overlay.
Process cleanup follows the paired Node's acknowledged restart semantics.
"""
import atexit
import subprocess
import threading
import time
from contextlib import contextmanager
from copy import deepcopy

from app.xray.core import XRayCore


class MainCoreError(RuntimeError):
    def __init__(self, code, status=503):
        self.code, self.status = code, status
        super().__init__(code)


class ManagedMainCore(XRayCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lifecycle_lock = threading.Lock()
        self._last_config = None
        self._logs_thread = None
        self._input_thread = None
        atexit.register(self.stop)

    @contextmanager
    def change(self):
        if not self.lifecycle_lock.acquire(blocking=False):
            raise MainCoreError("MAIN_CORE_BUSY", 409)
        self.restarting = True
        try:
            yield
        finally:
            self.restarting = False
            self.lifecycle_lock.release()

    def _runtime(self, base):
        from app.db import GetDB
        from app.xray.main_egress import read_profile, for_main
        with GetDB() as db:
            # A missing migration/decryption error is not permission to bypass
            # a configured proxy. Recovery must not silently fall back DIRECT.
            profile = read_profile(db)
        return for_main(base, profile)

    def validate_config(self, config):
        try:
            result = subprocess.run([self.executable_path, "run", "-test", "-config", "stdin:"],
                input=config.to_json(), text=True, capture_output=True, env=self._env, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise MainCoreError("MAIN_PREFLIGHT_FAILED", 422) from None
        if result.returncode != 0:
            raise MainCoreError("MAIN_PREFLIGHT_FAILED", 422)

    def _launch(self, config):
        process = subprocess.Popen([self.executable_path, "run", "-config", "stdin:"],
            env=self._env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        self.process = process
        # Capture this generation only. stderr is merged so neither pipe can
        # deadlock while starting or stopping a replacement.
        def read_logs():
            try:
                for line in process.stdout:
                    value = line.strip()
                    self._logs_buffer.append(value)
                    for buffer in list(self._temp_log_buffers.values()):
                        buffer.append(value)
            except (OSError, ValueError):
                pass
        self._logs_thread = threading.Thread(target=read_logs, daemon=True)
        self._logs_thread.start()
        written = threading.Event()
        failed = []
        def write_config():
            try:
                process.stdin.write(config.to_json())
                process.stdin.flush()
                process.stdin.close()
            except (OSError, ValueError):
                failed.append(True)
            finally:
                written.set()
        self._input_thread = threading.Thread(target=write_config, daemon=True)
        self._input_thread.start()
        if not written.wait(5) or failed:
            raise MainCoreError("MAIN_CORE_NOT_READY")

    def _wait_ready(self, config):
        from xray_api import XRay
        client = XRay(config.api_host, config.api_port)
        deadline = time.monotonic() + 5
        try:
            while time.monotonic() < deadline:
                if not self.started:
                    break
                try:
                    client.get_sys_stats(timeout=1)
                    time.sleep(0.15)
                    if self.started:
                        return
                except Exception:
                    time.sleep(0.1)
        finally:
            client._channel.close()
        raise MainCoreError("MAIN_CORE_NOT_READY")

    def _stop(self):
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        else:
            process.wait(timeout=3)
        self.process = None
        if self._logs_thread is not None:
            self._logs_thread.join(timeout=2)
        if self._input_thread is not None:
            self._input_thread.join(timeout=2)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        for callback in self._on_stop_funcs:
            threading.Thread(target=callback, daemon=True).start()

    def _ready(self, runtime):
        self._launch(runtime)
        self._wait_ready(runtime)
        self._last_config = deepcopy(runtime)
        for callback in self._on_start_funcs:
            threading.Thread(target=callback, daemon=True).start()

    def replace_runtime(self, runtime, rollback_config=None):
        """Caller holds change(); preflight leaves the working process intact."""
        self.validate_config(runtime)
        previous = rollback_config if rollback_config is not None else self._last_config
        self._stop()
        try:
            self._ready(runtime)
        except Exception:
            try:
                self._stop()
                if previous is None:
                    raise MainCoreError("MAIN_NO_PREVIOUS_CONFIG")
                self._ready(previous)
            except Exception:
                raise MainCoreError("MAIN_APPLY_FAILED_ROLLBACK_FAILED") from None
            raise MainCoreError("MAIN_APPLY_FAILED_ROLLED_BACK", 502) from None

    def start(self, config):
        with self.change():
            if self.started:
                raise MainCoreError("MAIN_CORE_BUSY", 409)
            runtime = self._runtime(config)
            self.validate_config(runtime)
            try:
                self._ready(runtime)
            except Exception:
                self._stop()
                raise

    def restart(self, config):
        with self.change():
            self.replace_runtime(self._runtime(config))

    def stop(self):
        with self.lifecycle_lock:
            self._stop()
