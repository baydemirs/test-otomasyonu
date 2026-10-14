"""CanRat's UIA controls through pywinauto; no lifecycle ownership here."""
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
import time

TARGET_ID = 'MainWindow.centralwidget.cboxAppendRecieved'
START_ID = 'MainWindow.centralwidget.btnStart'
STATE = {0: 'Off', 1: 'On'}
_KERNEL = ctypes.WinDLL('kernel32', use_last_error=True)
_KERNEL.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_KERNEL.OpenProcess.restype = wintypes.HANDLE
_KERNEL.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.c_void_p, ctypes.c_void_p]
_KERNEL.GetProcessTimes.restype = wintypes.BOOL
_KERNEL.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
_KERNEL.QueryFullProcessImageNameW.restype = wintypes.BOOL
_KERNEL.CloseHandle.argtypes = [wintypes.HANDLE]


class FileTime(ctypes.Structure):
    _fields_ = [('low', wintypes.DWORD), ('high', wintypes.DWORD)]


_EPOCH_DELTA = (datetime(1601, 1, 1, tzinfo=timezone.utc) -
                datetime(1, 1, 1, tzinfo=timezone.utc)).days * 86400 * 10_000_000


def process_identity(pid):
    """Independent PID/start/path check before connecting to the UIA tree."""
    handle = _KERNEL.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), 'OpenProcess failed')
    try:
        created = FileTime()
        exited, kernel, user = FileTime(), FileTime(), FileTime()
        if not _KERNEL.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                        ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError(ctypes.get_last_error(), 'GetProcessTimes failed')
        path = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(path))
        if not _KERNEL.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(length)):
            raise OSError(ctypes.get_last_error(), 'QueryFullProcessImageNameW failed')
        return {'pid': pid,
                'start_ticks': str(_EPOCH_DELTA + (created.high << 32) + created.low),
                'path': str(Path(path.value).resolve())}
    finally:
        _KERNEL.CloseHandle(handle)


def connect(pid, start_ticks, exe):
    from pywinauto import Desktop
    identity = process_identity(pid)
    if identity['start_ticks'] != str(start_ticks) or Path(identity['path']).resolve() != Path(exe).resolve():
        raise ValueError('PID/başlangıç zamanı/EXE yolu eşleşmiyor.')
    windows = Desktop(backend='uia').windows(process=pid, top_level_only=True, visible_only=True)
    if len(windows) != 1 or windows[0].element_info.process_id != pid:
        raise ValueError('Tek görünür CanRat ana penceresi bulunamadı.')
    return windows[0], identity


def unique_control(window, automation_id, control_type):
    matches = [control for control in window.descendants()
               if control.element_info.automation_id == automation_id]
    if len(matches) != 1:
        raise ValueError(f'Kontrol bulunamadı veya benzersiz değil: {automation_id}; sayı={len(matches)}')
    control = matches[0]
    if control.element_info.control_type != control_type:
        raise ValueError(f'Beklenmeyen kontrol türü: {automation_id}')
    return control


def state(control):
    value = control.get_toggle_state()
    if value not in STATE:
        raise ValueError(f'Belirsiz ToggleState: {value}')
    return STATE[value]


def stable_state(control):
    first = state(control)
    time.sleep(0.15)
    second = state(control)
    if first != second:
        raise ValueError(f'Kararsız ToggleState: {first} -> {second}')
    return second


def guard(window):
    # Qt exposes this QPushButton as a UIA CheckBox with TogglePattern.
    start = unique_control(window, START_ID, 'CheckBox')
    if start.element_info.class_name != 'QPushButton':
        raise ValueError('Start kontrolü beklenen QPushButton değil.')
    current = state(start)
    name = start.element_info.name
    return {'toggle_state': current, 'name': name,
            'active': current == 'On' or name == 'Stop',
            'idle': current == 'Off' and name == 'Start'}


def checkbox(window):
    control = unique_control(window, TARGET_ID, 'CheckBox')
    if control.element_info.class_name != 'QCheckBox' or not control.is_enabled() or not control.is_visible():
        raise ValueError('Hedef etkin/görünür QCheckBox değil.')
    return control


def wait_state(control, expected, seconds=2):
    deadline = time.monotonic() + seconds
    consecutive = 0
    while time.monotonic() < deadline:
        current = state(control)
        consecutive = consecutive + 1 if current == expected else 0
        if consecutive >= 2:
            return current
        time.sleep(0.1)
    raise TimeoutError(f'Beklenen ToggleState kararlı doğrulanamadı: {expected}')
