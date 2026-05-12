import ctypes

_dwmapi = ctypes.windll.dwmapi
_dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT

_DWMWA_NCRENDERING_POLICY = 2
_DWMNCRP_DISABLED = 2
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWCP_DONOTROUND = 1
_DWMWA_BORDER_COLOR = 34
_DWMWA_COLOR_NONE = 0xFFFFFFFE
_DWMWA_SYSTEMBACKDROP_TYPE = 38
_DWMSBT_NONE = 1


def disable_dwm_frame(hwnd: int):
    for attr, val_type, val in [
        (_DWMWA_NCRENDERING_POLICY, ctypes.c_int, _DWMNCRP_DISABLED),
        (_DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.c_int, _DWMWCP_DONOTROUND),
        (_DWMWA_BORDER_COLOR, ctypes.c_uint, _DWMWA_COLOR_NONE),
        (_DWMWA_SYSTEMBACKDROP_TYPE, ctypes.c_int, _DWMSBT_NONE),
    ]:
        v = val_type(val)
        _dwmapi.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(v), ctypes.sizeof(v)
        )
