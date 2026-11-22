"""
Local IPC protocol for Smoky Velvet daemon and CLI control.
Uses a fast, user-private UNIX domain socket.
"""
from __future__ import annotations
import json
import logging
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform.startswith("win")
WINDOWS_IPC_PORT = 49753

def get_socket_path() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and Path(runtime_dir).exists():
        return Path(runtime_dir) / "smoky-velvet.sock"
    return Path("/tmp/smoky-velvet.sock")

class IpcServer:
    def __init__(self, command_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.command_handler = command_handler
        self.socket_path = get_socket_path()
        self._server_sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

    def start(self) -> None:
        if self._is_running:
            return

        if IS_WINDOWS:
            try:
                self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._server_sock.bind(("127.0.0.1", WINDOWS_IPC_PORT))
                self._server_sock.listen(5)
                self._server_sock.settimeout(1.0)
                self._stop_event.clear()
                self._is_running = True
                self._thread = threading.Thread(target=self._accept_loop, daemon=True, name="IpcServer")
                self._thread.start()
                logger.info(f"Smoky Velvet IPC server listening on: 127.0.0.1:{WINDOWS_IPC_PORT}")
            except Exception as e:
                logger.error(f"Failed to start Windows IPC server: {e}")
            return

        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except Exception:
                pass

        try:
            self._server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server_sock.bind(str(self.socket_path))
            self._server_sock.listen(5)
            self._server_sock.settimeout(1.0)
            self._stop_event.clear()
            self._is_running = True
            self._thread = threading.Thread(target=self._accept_loop, daemon=True, name="IpcServer")
            self._thread.start()
            logger.info(f"Smoky Velvet IPC server listening on: {self.socket_path}")
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")

    def stop(self) -> None:
        self._stop_event.set()
        self._is_running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None

        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except Exception:
                pass

    def _accept_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                conn, _ = self._server_sock.accept() # type: ignore
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                return
            req = json.loads(data)
            resp = self.command_handler(req)
            conn.sendall(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            try:
                err_resp = {"status": "error", "message": str(e)}
                conn.sendall(json.dumps(err_resp).encode('utf-8'))
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


class IpcClient:
    """Client used by CLI and GUI to talk to running daemon."""
    @staticmethod
    def send_command(command: Dict[str, Any], timeout: float = 2.0) -> Dict[str, Any]:
        if IS_WINDOWS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect(("127.0.0.1", WINDOWS_IPC_PORT))
                sock.sendall(json.dumps(command).encode('utf-8'))
                data = sock.recv(4096).decode('utf-8')
                return json.loads(data)
            except Exception as e:
                return {"status": "error", "message": f"Smoky Velvet is not running on 127.0.0.1:{WINDOWS_IPC_PORT} ({e})"}
            finally:
                sock.close()

        sock_path = get_socket_path()
        if not sock_path.exists():
            return {"status": "error", "message": "Smoky Velvet is not running."}

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect(str(sock_path))
            sock.sendall(json.dumps(command).encode('utf-8'))
            data = sock.recv(4096).decode('utf-8')
            return json.loads(data)
        except Exception as e:
            return {"status": "error", "message": f"IPC communication error: {e}"}
        finally:
            sock.close()
