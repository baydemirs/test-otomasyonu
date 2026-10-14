"""Salt okunur Windows erişim tanısı; token, ACL veya masaüstü değiştirmez."""
import argparse
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import uuid


def collect(target_pid):
    if sys.platform != 'win32':
        raise RuntimeError('Windows gereklidir')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    advapi = c.WinDLL('advapi32', use_last_error=True)
    user = c.WinDLL('user32', use_last_error=True)

    def bind(dll, name, args, result):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, result
        return fn

    current = bind(kernel, 'GetCurrentProcess', [], w.HANDLE)
    pid_fn = bind(kernel, 'GetCurrentProcessId', [], w.DWORD)
    tid_fn = bind(kernel, 'GetCurrentThreadId', [], w.DWORD)
    open_process = bind(kernel, 'OpenProcess', [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
    close = bind(kernel, 'CloseHandle', [w.HANDLE], w.BOOL)
    session_fn = bind(kernel, 'ProcessIdToSessionId', [w.DWORD, c.POINTER(w.DWORD)], w.BOOL)
    path_fn = bind(kernel, 'QueryFullProcessImageNameW', [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)], w.BOOL)
    arch_fn = bind(kernel, 'IsWow64Process2', [w.HANDLE, c.POINTER(w.WORD), c.POINTER(w.WORD)], w.BOOL)
    open_token = bind(advapi, 'OpenProcessToken', [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL)
    token_fn = bind(advapi, 'GetTokenInformation', [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)], w.BOOL)
    sid_string_fn = bind(advapi, 'ConvertSidToStringSidW', [c.c_void_p, c.POINTER(w.LPWSTR)], w.BOOL)
    local_free = bind(kernel, 'LocalFree', [c.c_void_p], c.c_void_p)
    lookup_fn = bind(advapi, 'LookupAccountSidW', [w.LPCWSTR, c.c_void_p, w.LPWSTR, c.POINTER(w.DWORD), w.LPWSTR, c.POINTER(w.DWORD), c.POINTER(w.DWORD)], w.BOOL)
    desktop_fn = bind(user, 'GetThreadDesktop', [w.DWORD], w.HANDLE)
    station_fn = bind(user, 'GetProcessWindowStation', [], w.HANDLE)
    object_fn = bind(user, 'GetUserObjectInformationW', [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)], w.BOOL)

    class SidAttributes(c.Structure):
        _fields_ = [('sid', c.c_void_p), ('attributes', w.DWORD)]

    def error():
        code = c.get_last_error()
        return {'winerror': code, 'message': c.FormatError(code).strip()}

    def object_name(handle):
        buf, size = c.create_unicode_buffer(512), w.DWORD()
        if not handle or not object_fn(handle, 2, buf, c.sizeof(buf), c.byref(size)):
            return error()
        return buf.value

    def token_info(token, kind):
        needed = w.DWORD()
        token_fn(token, kind, None, 0, c.byref(needed))
        if not needed.value:
            return None, error()
        buf = c.create_string_buffer(needed.value)
        if not token_fn(token, kind, buf, len(buf), c.byref(needed)):
            return None, error()
        return buf, None

    def sid_text(sid):
        value = w.LPWSTR()
        if not sid_string_fn(sid, c.byref(value)):
            return error()
        try:
            return value.value
        finally:
            local_free(c.cast(value, c.c_void_p))

    def read_token(handle):
        token = w.HANDLE()
        if not open_token(handle, 8, c.byref(token)):  # TOKEN_QUERY only
            return {'open_token_error': error()}
        result = {}
        try:
            for name, kind in [('user', 1), ('integrity', 25), ('elevation', 20), ('elevation_type', 18), ('ui_access', 26), ('session', 12)]:
                buf, err = token_info(token, kind)
                if err:
                    result[name] = err
                elif name in ('user', 'integrity'):
                    sid = c.cast(buf, c.POINTER(SidAttributes)).contents.sid
                    result[name + '_sid'] = sid_text(sid)
                    if name == 'user':
                        account, domain = c.create_unicode_buffer(512), c.create_unicode_buffer(512)
                        na, nd, usage = w.DWORD(512), w.DWORD(512), w.DWORD()
                        if lookup_fn(None, sid, account, c.byref(na), domain, c.byref(nd), c.byref(usage)):
                            result['account'] = domain.value + '\\' + account.value
                        else:
                            result['account_error'] = error()
                else:
                    result[name] = c.cast(buf, c.POINTER(w.DWORD)).contents.value
            return result
        finally:
            close(token)

    def process_info(pid, handle):
        result = {'pid': pid}
        session = w.DWORD()
        result['session'] = session.value if session_fn(pid, c.byref(session)) else error()
        if not handle:
            result['open_process_error'] = error()
            return result
        path, count = c.create_unicode_buffer(32768), w.DWORD(32768)
        result['path'] = path.value if path_fn(handle, 0, path, c.byref(count)) else error()
        process_machine, native_machine = w.WORD(), w.WORD()
        if arch_fn(handle, c.byref(process_machine), c.byref(native_machine)):
            result['architecture'] = {'process_machine': process_machine.value, 'native_machine': native_machine.value}
        else:
            result['architecture'] = error()
        result['token'] = read_token(handle)
        return result

    target_handle = open_process(0x1000, False, target_pid)  # QUERY_LIMITED_INFORMATION
    target_error = error() if not target_handle else None
    try:
        own = process_info(pid_fn(), current())
        target = process_info(target_pid, target_handle)
        if target_error:
            target['open_process_error'] = target_error
    finally:
        if target_handle:
            close(target_handle)

    # Enumerate HWND metadata on the current desktop, retain only target PID.
    # No UIA tree, unrelated title, window activation or input is collected.
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    enum_fn = bind(user, 'EnumWindows', [callback_type, w.LPARAM], w.BOOL)
    window_pid_fn = bind(user, 'GetWindowThreadProcessId', [w.HWND, c.POINTER(w.DWORD)], w.DWORD)
    visible_fn = bind(user, 'IsWindowVisible', [w.HWND], w.BOOL)
    windows = []

    @callback_type
    def visit(hwnd, unused):
        window_pid = w.DWORD()
        thread_id = window_pid_fn(hwnd, c.byref(window_pid))
        if window_pid.value == target_pid:
            windows.append({'hwnd': int(hwnd), 'thread_id': thread_id, 'visible': bool(visible_fn(hwnd)), 'desktop': object_name(desktop_fn(thread_id))})
        return True

    c.set_last_error(0)
    enum_ok = enum_fn(visit, 0)
    return {
        'schema_version': 1, 'kind': 'READ_ONLY_WINDOWS_ACCESS_DIAGNOSTIC',
        'time_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'python_bits': c.sizeof(c.c_void_p) * 8,
        'command': [sys.executable, *sys.argv],
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'current_process': own, 'target_process': target,
        'current_window_station': object_name(station_fn()),
        'current_desktop': object_name(desktop_fn(tid_fn())),
        'target_windows_on_current_desktop': windows,
        'enum_windows_succeeded': bool(enum_ok),
        'enum_windows_error': None if enum_ok else error(),
        'test_result': None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-pid', type=int, required=True)
    parser.add_argument('--label', choices=['sandbox', 'supported'], required=True)
    args = parser.parse_args()
    if args.target_pid <= 0:
        parser.error('PID pozitif olmalıdır')
    report = collect(args.target_pid)
    report['execution_label'] = args.label
    folder = Path(__file__).resolve().parents[2] / 'raporlar' / 'kosular' / ('erisim-' + uuid.uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    path = folder / 'windows-erisim.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(path)
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
