"""Take the repo's PCB pictures from the running Altium window, the same way every time.

    python tools/pcb_shots.py            all six pictures -> screenshots/
    python tools/pcb_shots.py flat       only the two straight-down 3D views
    python tools/pcb_shots.py tilt       only the two tilted 3D views
    python tools/pcb_shots.py 2d         only the two 2D views
    python tools/pcb_shots.py grab NAME  no keys sent: just crop what is on screen now -> screenshots/NAME.jpg

Before running: Altium open and maximised with DebugBoard.PcbDoc as the active tab. Another window may float over
Altium (the picture is read from Altium's own window), but keep it off the middle of the PCB view, where the mouse works.
Do not touch the mouse or keyboard while it runs (about 40 s; it stops by itself if another window becomes active): it drives Altium with its own shortcut keys
(3 / 2 = 3D / 2D, 0 = straight down, V F = fit board, V B = flip board) and tilts the 3D view
with a Shift + right-button drag. After Fit Board the view is zoomed out two wheel notches (Ctrl + wheel), so the floating toolbar at the top of
the view and the layer tabs at the bottom never cover the board; each picture is then cropped to the board plus 12 pixels.

Pictures: V1_pcb_top.jpg, V1_pcb_bottom.jpg (straight down, 3D; the bottom one is saved in landscape), V1_pcb_top_3d.jpg, V1_pcb_bottom_3d.jpg (tilted),
V1_pcb_2d_top.png, V1_pcb_2d_bottom.png (2D layer view).
"""
import ctypes, os, sys, time
import numpy as np
from ctypes import wintypes
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'screenshots')
# Shift + right-drag steps in screen pixels (per 1920-wide screen), from a straight-down view. About 6.8 pixels turn the
# board 1 degree about the screen's horizontal (vertical drag) or vertical (horizontal drag) axis. To turn the board
# in its own plane: stand it on edge (90 degrees), turn it, lean it back down. Result: turned ~58 degrees, seen ~57 degrees off vertical.
TILT = [(0, -615), (-395, 0), (0, 225)]
BOTTOM_TURN = -90                 # the straight-down back view is saved turned a quarter clockwise: the bottom artwork and title are drawn for landscape
MARGIN = 12                    # crop margin around the board in pixels: tight, so the floating toolbar above the board stays out of the picture
u = ctypes.windll.user32
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass
VK = {'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'pgdn': 0x22, 'pgup': 0x21}

def altium():
    found = []
    def cb(h, _):
        n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
        if 'Altium Designer' in b.value and u.IsWindowVisible(h): found.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
    if not found: sys.exit('Altium Designer is not running')
    return found[0]
HWND = None
def pid_of(h):
    p = ctypes.c_ulong(0); u.GetWindowThreadProcessId(ctypes.c_void_p(h), ctypes.byref(p)); return p.value
def front(h):
    global HWND
    HWND = h
    for _ in range(5):
        u.ShowWindow(h, 3); u.keybd_event(VK['ctrl'], 0, 0, 0); u.SetForegroundWindow(h); u.keybd_event(VK['ctrl'], 0, 2, 0); time.sleep(1.0)   # (a lone Alt would open the menu bar and eat the next key)
        if pid_of(u.GetForegroundWindow()) == pid_of(h): return
    sys.exit('Could not bring Altium to the front: nothing was sent to it. Click the Altium window and run again.')
def guard():
    """Never type or click into another program: stop at once if Altium is not the active window."""
    if pid_of(u.GetForegroundWindow()) != pid_of(HWND):                # Altium's own pop-up windows (rotation sphere, heads-up display) are fine
        u.keybd_event(VK['shift'], 0, 2, 0); u.mouse_event(0x0010, 0, 0, 0, 0)
        sys.exit('Altium is no longer the active window: stopped without sending anything more.')
def rect(h):
    r = (ctypes.c_long * 4)(); u.GetWindowRect(h, r); return [max(v, 0) for v in r]
def key(k, wait=0.6):
    guard(); v = VK.get(k) or ord(k.upper()); u.keybd_event(v, 0, 0, 0); time.sleep(0.05); u.keybd_event(v, 0, 2, 0); time.sleep(wait)
def keys(seq, wait=1.5):
    for k in seq[:-1]: key(k, 0.35)
    key(seq[-1], wait)
def drag(x, y, dx, dy):
    """Shift + right-button drag: Altium's 3D rotation, started on the centre dot of its rotation sphere."""
    guard(); u.SetCursorPos(x, y); time.sleep(0.3)
    u.keybd_event(VK['shift'], 0, 0, 0); time.sleep(0.5)
    u.mouse_event(0x0008, 0, 0, 0, 0); time.sleep(0.2)                 # right button down
    for i in range(1, 31):
        u.SetCursorPos(int(x + dx * i / 30), int(y + dy * i / 30)); time.sleep(0.02)
    time.sleep(0.2); u.mouse_event(0x0010, 0, 0, 0, 0); time.sleep(0.2)   # right button up
    u.keybd_event(VK['shift'], 0, 2, 0); time.sleep(0.5)

g32 = ctypes.windll.gdi32
for _f in (u.GetWindowDC, g32.CreateCompatibleDC, g32.CreateCompatibleBitmap, g32.SelectObject): _f.restype = ctypes.c_void_p
class _BIH(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_long), ('biHeight', ctypes.c_long), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD),
                ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD), ('a', ctypes.c_long), ('b', ctypes.c_long), ('c', wintypes.DWORD), ('d', wintypes.DWORD)]
def window_image(h):
    """Picture of the Altium window itself (PrintWindow), so a window floating on top of it does not get into the picture.
    Returns the image and the screen position of its top-left corner."""
    r = wintypes.RECT(); u.GetWindowRect(ctypes.c_void_p(h), ctypes.byref(r)); w, hh = r.right - r.left, r.bottom - r.top
    wdc = u.GetWindowDC(ctypes.c_void_p(h)); mdc = g32.CreateCompatibleDC(ctypes.c_void_p(wdc)); bmp = g32.CreateCompatibleBitmap(ctypes.c_void_p(wdc), w, hh)
    g32.SelectObject(ctypes.c_void_p(mdc), ctypes.c_void_p(bmp)); u.PrintWindow(ctypes.c_void_p(h), ctypes.c_void_p(mdc), 2)
    bi = _BIH(); bi.biSize = ctypes.sizeof(_BIH); bi.biWidth = w; bi.biHeight = -hh; bi.biPlanes = 1; bi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * hh * 4)
    g32.GetDIBits(ctypes.c_void_p(mdc), ctypes.c_void_p(bmp), 0, hh, buf, ctypes.byref(bi), 0)
    g32.DeleteObject(ctypes.c_void_p(bmp)); g32.DeleteDC(ctypes.c_void_p(mdc)); u.ReleaseDC(ctypes.c_void_p(h), ctypes.c_void_p(wdc))
    return Image.frombuffer('RGBA', (w, hh), buf, 'raw', 'BGRA', 0, 1).convert('RGB'), (r.left, r.top)

def biggest(mask):
    """Bounding box of the largest connected blob of a mask (worked out on a 4x smaller copy)."""
    m = mask[::4, ::4]; best = None; left = m.copy()
    while left.any():
        ys, xs = np.nonzero(left); seed = np.zeros_like(m); seed[ys[0], xs[0]] = True
        while True:
            g = seed.copy()
            g[1:] |= seed[:-1]; g[:-1] |= seed[1:]; g[:, 1:] |= seed[:, :-1]; g[:, :-1] |= seed[:, 1:]
            g &= m
            if (g == seed).all(): break
            seed = g
        left &= ~seed
        if best is None or seed.sum() > best.sum(): best = seed
        if left.sum() < best.sum(): break
    ys, xs = np.nonzero(best)
    return int(xs.min()) * 4, int(ys.min()) * 4, int(xs.max()) * 4 + 4, int(ys.max()) * 4 + 4

def board_mask(a, mode):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if mode == '3d': return (g > r + 25) & (g > b + 25)                 # the green board
    v = a[int(a.shape[0] * 0.12):int(a.shape[0] * 0.93):3, int(a.shape[1] * 0.18):int(a.shape[1] * 0.96):3].reshape(-1, 3)
    cols, counts = np.unique(v[:, 0] * 65536 + v[:, 1] * 256 + v[:, 2], return_counts=True); c = int(cols[counts.argmax()])
    view = np.array([c >> 16, (c >> 8) & 255, c & 255])               # 2D view background = the most common colour in the view
    mask = (np.abs(a - view).sum(axis=2) > 40)
    mask[:, :int(a.shape[1] * 0.16)] = False; mask[:int(a.shape[0] * 0.10)] = False; mask[int(a.shape[0] * 0.95):] = False
    mask[:, int(a.shape[1] * 0.97):] = False
    return mask

def grab(h, name, mode, turn=0):
    for attempt in (0, 1):
        im, (x0, y0) = window_image(h); a = np.asarray(im).astype(int)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        if attempt == 0:                                               # first look only finds the board, to park the cursor beside it
            bx0, by0, bx1, by1 = biggest(board_mask(a, mode))
            px = bx1 + int((bx1 - bx0) * 0.30) + 40
            if px > a.shape[1] * 0.74: px = max(bx0 - int((bx1 - bx0) * 0.30) - 40, int(a.shape[1] * 0.14))
            u.SetCursorPos(x0 + px, y0 + min(by1 + 20, a.shape[0] - 60)); time.sleep(1.3)
    mask = board_mask(a, mode)
    bx0, by0, bx1, by1 = biggest(mask)
    mx = my = MARGIN
    box = (max(bx0 - mx, 0), max(by0 - my, 0), min(bx1 + mx, a.shape[1]), min(by1 + my, a.shape[0]))
    out = os.path.join(OUT, name); crop = im.crop(box)
    if turn: crop = crop.rotate(turn, expand=True)
    crop.save(out, quality=93) if name.endswith('.jpg') else crop.save(out)
    print('saved', name, crop.size, 'board box', (bx0, by0, bx1, by1))
    return (x0 + (bx0 + bx1) // 2, y0 + (by0 + by1) // 2)

def fit(h, centre=None, notches=2):
    """Fit Board fills the view, where the floating toolbar and the layer tabs overlap the board: zoom out a little after it."""
    keys('vf'); x0, y0, x1, y1 = rect(h)
    cx, cy = centre or (x0 + int((x1 - x0) * 0.56), y0 + (y1 - y0) // 2)
    u.SetCursorPos(cx, cy); time.sleep(0.3); guard()
    u.keybd_event(VK['ctrl'], 0, 0, 0); time.sleep(0.5)
    for _ in range(notches): u.mouse_event(0x0800, 0, 0, ctypes.c_ulong(-120 & 0xFFFFFFFF), 0); time.sleep(0.5)   # Ctrl + wheel: 9 % smaller per notch
    u.keybd_event(VK['ctrl'], 0, 2, 0); time.sleep(1.2)
    return cx, cy

def main(what):
    h = altium(); front(h); os.makedirs(OUT, exist_ok=True)
    if what == 'grab': grab(h, sys.argv[2] + '.jpg', '3d'); return
    if what == 'try':                                                  # calibration: python tools/pcb_shots.py try dx,dy dx,dy ...
        x0, y0, x1, y1 = rect(h); s = (x1 - x0) / 1920.0
        key('3', 2.5); key('0', 2.0); c = fit(h); c = grab(h, '_try0.jpg', '3d')
        for d in sys.argv[2:]:
            dx, dy = (int(v) for v in d.split(',')); drag(c[0], c[1], int(dx * s), int(dy * s))
        fit(h, c, 3); grab(h, '_try.jpg', '3d'); keys('vb', 2.5); fit(h, c, 3); grab(h, '_try_b.jpg', '3d'); keys('vb', 2.5); return
    x0, y0, x1, y1 = rect(h); s = (x1 - x0) / 1920.0
    if what in ('all', 'flat', 'tilt'):
        key('3', 2.5); key('0', 2.0); c = fit(h)
        if what in ('all', 'flat'):
            c = grab(h, 'V1_pcb_top.jpg', '3d')
            keys('vb', 2.5); fit(h, c); grab(h, 'V1_pcb_bottom.jpg', '3d', BOTTOM_TURN); keys('vb', 2.5); fit(h, c)
        if what in ('all', 'tilt'):
            for dx, dy in TILT: drag(c[0], c[1], int(dx * s), int(dy * s))
            fit(h, c); grab(h, 'V1_pcb_top_3d.jpg', '3d')
            keys('vb', 2.5); fit(h, c); grab(h, 'V1_pcb_bottom_3d.jpg', '3d'); keys('vb', 2.5)
            key('0', 2.0); fit(h, c)                                    # leave the view straight down
    if what in ('all', '2d'):
        key('2', 2.5); fit(h); grab(h, 'V1_pcb_2d_top.png', '2d')
        keys('vb', 2.5); fit(h); grab(h, 'V1_pcb_2d_bottom.png', '2d'); keys('vb', 2.5)
        key('3', 2.5)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
