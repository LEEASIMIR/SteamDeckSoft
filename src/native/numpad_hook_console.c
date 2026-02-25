/*
 * Console version of numpad_hook for debugging.
 * Shows output directly in the console.
 *
 * Compile: gcc -O2 -o numpad_hook_console.exe numpad_hook_console.c -luser32 -lkernel32
 */

#include <windows.h>
#include <stdio.h>

static HHOOK g_hook = NULL;
static volatile LONG g_any_keys = 0;
static volatile LONG g_suppressed = 0;
static volatile int g_numlock_off = 0;

static int is_numpad_nav(int scan) {
    return (scan >= 71 && scan <= 73) ||
           (scan >= 75 && scan <= 77) ||
           (scan >= 79 && scan <= 82);
}

static LRESULT CALLBACK hook_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode >= 0) {
        KBDLLHOOKSTRUCT *kb = (KBDLLHOOKSTRUCT *)lParam;
        int vk   = (int)kb->vkCode;
        int scan = (int)kb->scanCode;
        int flags = (int)kb->flags;
        int injected = flags & 0x10;
        int extended = flags & 0x01;

        InterlockedIncrement(&g_any_keys);

        if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
            if (vk == 0x90) {
                int will_be_on = !(GetKeyState(0x90) & 1);
                g_numlock_off = !will_be_on;
            }
            if (g_numlock_off && !injected && !extended && is_numpad_nav(scan)) {
                InterlockedIncrement(&g_suppressed);
                printf("SUPPRESS scan=%d vk=0x%02X\n", scan, vk);
                fflush(stdout);
                return 1;
            }
        } else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
            if (g_numlock_off && !injected && !extended && is_numpad_nav(scan)) {
                return 1;
            }
        }
    }
    return CallNextHookEx(g_hook, nCode, wParam, lParam);
}

int main(void)
{
    MSG msg;

    g_numlock_off = !(GetKeyState(0x90) & 1);
    printf("numlock_off=%d\n", g_numlock_off);

    g_hook = SetWindowsHookExW(13, hook_proc, GetModuleHandleW(NULL), 0);
    if (!g_hook) {
        printf("SetWindowsHookExW FAILED! err=%lu\n", GetLastError());
        return 1;
    }
    printf("Hook installed. Press numpad keys (Num Lock OFF). Ctrl+C to stop.\n");
    fflush(stdout);

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    UnhookWindowsHookEx(g_hook);
    return 0;
}
