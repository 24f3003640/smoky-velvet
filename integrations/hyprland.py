"""
Hyprland IPC event socket integration.
Listens to activewindow, workspace, and fullscreen events via .socket2.sock.
"""
from __future__ import annotations
import logging
import os
import socket
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class HyprlandEventListener:
    def __init__(
        self,
        on_active_window: Optional[Callable[[str, str], None]] = None,
        on_workspace_change: Optional[Callable[[str], None]] = None,
        on_fullscreen: Optional[Callable[[bool], None]] = None
    ):
        self.on_active_window = on_active_window
        self.on_workspace_change = on_workspace_change
        self.on_fullscreen = on_fullscreen

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

    @staticmethod
    def get_socket_path() -> Optional[Path]:
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        runtime = os.environ.get("XDG_RUNTIME_DIR")
        if not sig or not runtime:
            return None
        sock = Path(runtime) / "hypr" / sig / ".socket2.sock"
        return sock if sock.exists() else None

    @property
    def is_available(self) -> bool:
        return self.get_socket_path() is not None

    def start(self) -> bool:
        if self._is_running:
            return True

        sock_path = self.get_socket_path()
        if not sock_path:
            logger.warning("Hyprland event socket not available (non-Hyprland session).")
            return False

        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="HyprlandListener")
        self._thread.start()
        logger.info(f"Hyprland event listener active on: {sock_path}")
        return True

    def stop(self) -> None:
        self._stop_event.set()
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

    def _listen_loop(self) -> None:
        while not self._stop_event.is_set():
            sock_path = self.get_socket_path()
            if not sock_path:
                time.sleep(2.0)
                continue

            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(str(sock_path))
                sock.settimeout(2.0)
                buffer = ""

                while not self._stop_event.is_set():
                    try:
                        chunk = sock.recv(2048).decode('utf-8')
                        if not chunk:
                            break
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            self._handle_event_line(line.strip())
                    except socket.timeout:
                        continue
                    except Exception:
                        break

                sock.close()
            except Exception as e:
                logger.debug(f"Hyprland socket reconnecting in 2s: {e}")
                time.sleep(2.0)

    def _handle_event_line(self, line: str) -> None:
        if not line or ">>" not in line:
            return

        event_name, data = line.split(">>", 1)

        if event_name == "activewindow":
            # format: windowclass,windowtitle
            parts = data.split(",", 1)
            win_class = parts[0]
            win_title = parts[1] if len(parts) > 1 else ""
            if self.on_active_window:
                self.on_active_window(win_class, win_title)

        elif event_name == "workspace":
            # format: workspacename
            if self.on_workspace_change:
                self.on_workspace_change(data)

        elif event_name == "fullscreen":
            # format: 0 or 1
            if self.on_fullscreen:
                self.on_fullscreen(data == "1")
