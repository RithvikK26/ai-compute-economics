"""Check the installed production package and initial app without external sockets."""

import json
import socket
from pathlib import Path

from streamlit.testing.v1 import AppTest

from compute_economics.ui.service import ROOT


def deny_network(*args, **kwargs):
    raise AssertionError("Production smoke test attempted a network connection")


def main():
    assert ROOT == Path.cwd().resolve(), "Install the project editable from the repository root"
    assert (ROOT / "data/snapshots/2026-09-27/manifest.json").is_file()
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    app = AppTest.from_file(ROOT / "app.py", default_timeout=90).run()
    assert not app.exception
    assert len(app.download_button) == 7
    print(
        json.dumps(
            {
                "status": "PASS",
                "production_entrypoint": "app.py",
                "network": "blocked",
                "download_controls": 7,
            }
        )
    )


if __name__ == "__main__":
    main()
