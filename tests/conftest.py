"""Local compatibility helpers for the GenLayer direct test runner."""

import atexit
import os
import sys
import tempfile


_STDIN_TEMP_PATHS = []


def _windows_safe_inject_message_to_fd0(vm):
    """Keep the duplicated stdin file alive until VM cleanup on Windows."""
    from genlayer.py import calldata
    from genlayer.py.types import Address

    sender = Address(vm.sender) if isinstance(vm.sender, bytes) else vm.sender
    contract = (
        Address(vm._contract_address)
        if isinstance(vm._contract_address, bytes)
        else vm._contract_address
    )
    origin = Address(vm.origin) if isinstance(vm.origin, bytes) else vm.origin
    encoded = calldata.encode(
        {
            "contract_address": contract,
            "sender_address": sender,
            "origin_address": origin,
            "stack": [],
            "value": vm._value,
            "datetime": vm._datetime,
            "is_init": False,
            "chain_id": vm._chain_id,
            "entry_kind": 0,
            "entry_data": b"",
            "entry_stage_data": None,
        }
    )

    fd, path = tempfile.mkstemp()
    os.write(fd, encoded)
    os.lseek(fd, 0, os.SEEK_SET)
    vm._original_stdin_fd = os.dup(0)
    os.dup2(fd, 0)
    os.close(fd)
    _STDIN_TEMP_PATHS.append(path)


def _remove_stdin_temp_files():
    for path in _STDIN_TEMP_PATHS:
        try:
            os.unlink(path)
        except OSError:
            pass


if sys.platform == "win32":
    from gltest.direct import loader

    loader._inject_message_to_fd0 = _windows_safe_inject_message_to_fd0
    atexit.register(_remove_stdin_temp_files)
