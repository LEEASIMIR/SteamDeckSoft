/*
 * numpad_hook.dll — GIL-free keyboard hook with shared memory IPC.
 *
 * The hook callback lives in this DLL (required by Windows for
 * WH_KEYBOARD_LL to actually receive callbacks).  A separate
 * launcher exe (numpad_launcher.exe) loads this DLL in its own
 * process so the hook works even from PyInstaller-bundled apps.
 *
 * Communication with Python is via a named shared-memory region.
 *
 * Compile:
 *   gcc -shared -O2 -o numpad_hook.dll numpad_hook.c -luser32 -lkernel32
 */

#include <windows.h>
#include <stdlib.h>

/* ---- shared memory layout (must match Python) ------------------------- */

#define SHM_NAME  L"Local\\SteamDeckSoft_NumpadHook"
#define MAX_EVENTS 256

#pragma pack(push, 1)
typedef struct {
    volatile LONG ev_write;
    volatile LONG ev_read;
    volatile int  events[MAX_EVENTS];

    volatile LONG nl_changed;
    volatile int  nl_new_state;

    volatile int  passthrough;
    volatile int  numlock_off;
    volatile int  running;         /* Python sets to 0 → exit */

    /* debug */
    volatile LONG any_key_count;
    volatile LONG suppressed;
    volatile LONG numpad_seen;
    volatile LONG hook_ok;
} SharedData;
#pragma pack(pop)

/* ---- globals ---------------------------------------------------------- */

static HMODULE    g_dll_module = NULL;
static HHOOK      g_hook       = NULL;
static HANDLE     g_thread     = NULL;
static DWORD      g_thread_id  = 0;
static HANDLE     g_hMap       = NULL;
static SharedData *g_shm       = NULL;
static volatile int g_running  = 0;

/* ---- helpers ---------------------------------------------------------- */

static int is_numpad_nav(int scan) {
    return (scan >= 71 && scan <= 73) ||
           (scan >= 75 && scan <= 77) ||
           (scan >= 79 && scan <= 82);
}

/* ---- hook callback (pure C, in DLL) ----------------------------------- */

static LRESULT CALLBACK hook_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode >= 0 && g_shm) {
        KBDLLHOOKSTRUCT *kb = (KBDLLHOOKSTRUCT *)lParam;
        int vk       = (int)kb->vkCode;
        int scan     = (int)kb->scanCode;
        int flags    = (int)kb->flags;
        int injected = flags & 0x10;
        int extended = flags & 0x01;

        InterlockedIncrement(&g_shm->any_key_count);

        if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
            if (vk == 0x90) {
                int will_be_on = !(GetKeyState(0x90) & 1);
                g_shm->numlock_off  = !will_be_on;
                g_shm->nl_new_state = will_be_on;
                InterlockedExchange(&g_shm->nl_changed, 1);
            }

            if (is_numpad_nav(scan))
                InterlockedIncrement(&g_shm->numpad_seen);

            if (!g_shm->passthrough && g_shm->numlock_off &&
                !injected && !extended)
            {
                if (is_numpad_nav(scan)) {
                    LONG w    = g_shm->ev_write;
                    LONG next = (w + 1) % MAX_EVENTS;
                    if (next != g_shm->ev_read) {
                        g_shm->events[w] = scan;
                        InterlockedExchange(&g_shm->ev_write, next);
                    }
                    InterlockedIncrement(&g_shm->suppressed);
                    return 1;
                }
            }
        } else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
            if (!g_shm->passthrough && g_shm->numlock_off &&
                !injected && !extended)
            {
                if (is_numpad_nav(scan))
                    return 1;
            }
        }
    }
    return CallNextHookEx(g_hook, nCode, wParam, lParam);
}

/* ---- hook thread ------------------------------------------------------ */

static void CALLBACK check_running(HWND hwnd, UINT msg, UINT_PTR id, DWORD t)
{
    if (g_shm && !g_shm->running)
        PostQuitMessage(0);
    if (!g_running)
        PostQuitMessage(0);
}

static DWORD WINAPI hook_thread(LPVOID param)
{
    MSG msg;

    g_hook = SetWindowsHookExW(13 /*WH_KEYBOARD_LL*/,
                               hook_proc,
                               g_dll_module, 0);
    if (!g_hook) {
        if (g_shm) g_shm->hook_ok = 0;
        return 1;
    }
    if (g_shm) g_shm->hook_ok = 1;

    SetTimer(NULL, 0, 200, check_running);

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    UnhookWindowsHookEx(g_hook);
    g_hook = NULL;
    if (g_shm) g_shm->hook_ok = 0;
    return 0;
}

/* ---- exported API ----------------------------------------------------- */

__declspec(dllexport) int __cdecl start_hook(void)
{
    if (g_running) return 1;

    /* create shared memory */
    g_hMap = CreateFileMappingW(
        INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
        0, sizeof(SharedData), SHM_NAME);
    if (!g_hMap) return 0;

    g_shm = (SharedData *)MapViewOfFile(
        g_hMap, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));
    if (!g_shm) { CloseHandle(g_hMap); g_hMap = NULL; return 0; }

    ZeroMemory((void *)g_shm, sizeof(SharedData));
    g_shm->running     = 1;
    g_shm->numlock_off  = !(GetKeyState(0x90) & 1);

    g_running = 1;
    g_thread = CreateThread(NULL, 0, hook_thread, NULL, 0, &g_thread_id);
    if (!g_thread) {
        g_running = 0;
        UnmapViewOfFile((void *)g_shm); g_shm = NULL;
        CloseHandle(g_hMap); g_hMap = NULL;
        return 0;
    }
    return 1;
}

__declspec(dllexport) void __cdecl stop_hook(void)
{
    if (!g_running) return;
    g_running = 0;
    if (g_thread_id)
        PostThreadMessageW(g_thread_id, WM_QUIT, 0, 0);
    if (g_thread) {
        WaitForSingleObject(g_thread, 2000);
        CloseHandle(g_thread);
        g_thread = NULL;
    }
    g_thread_id = 0;

    if (g_shm) {
        UnmapViewOfFile((void *)g_shm);
        g_shm = NULL;
    }
    if (g_hMap) {
        CloseHandle(g_hMap);
        g_hMap = NULL;
    }
}

/* Legacy poll API (for direct ctypes usage without shared memory) */
__declspec(dllexport) int __cdecl poll_event(void)
{
    if (!g_shm) return -1;
    LONG r = g_shm->ev_read;
    if (r == g_shm->ev_write) return -1;
    int scan = g_shm->events[r];
    InterlockedExchange(&g_shm->ev_read, (r + 1) % MAX_EVENTS);
    return scan;
}

__declspec(dllexport) int __cdecl poll_numlock(void)
{
    if (!g_shm) return -1;
    if (InterlockedExchange(&g_shm->nl_changed, 0))
        return g_shm->nl_new_state;
    return -1;
}

__declspec(dllexport) void __cdecl set_passthrough(int value)
{
    if (g_shm)
        InterlockedExchange((volatile LONG *)&g_shm->passthrough, value);
}

__declspec(dllexport) int __cdecl is_numlock_on(void)
{
    return g_shm ? !g_shm->numlock_off : 0;
}

__declspec(dllexport) int __cdecl get_hook_status(void)
{
    return g_shm ? (int)g_shm->hook_ok : 0;
}

__declspec(dllexport) int __cdecl get_any_key_count(void)
{
    return g_shm ? (int)g_shm->any_key_count : 0;
}

__declspec(dllexport) int __cdecl get_suppressed_count(void)
{
    return g_shm ? (int)g_shm->suppressed : 0;
}

__declspec(dllexport) int __cdecl get_numpad_seen(void)
{
    return g_shm ? (int)g_shm->numpad_seen : 0;
}

__declspec(dllexport) int __cdecl get_numlock_off(void)
{
    return g_shm ? g_shm->numlock_off : 0;
}

/*
 * Entry point for rundll32.exe:
 *   rundll32.exe numpad_hook.dll,start_entry <parent_pid>
 *
 * Starts the hook and blocks until either:
 *   (a) Python sets shared memory "running" to 0, or
 *   (b) the parent process (identified by <parent_pid>) exits/crashes.
 * This ensures no orphaned rundll32 processes on abnormal termination.
 */
__declspec(dllexport) void CALLBACK start_entry(
    HWND hwnd, HINSTANCE hinst, LPSTR lpszCmdLine, int nCmdShow)
{
    DWORD parent_pid = 0;
    HANDLE parent_proc = NULL;

    /* Parse parent PID from command line */
    if (lpszCmdLine && lpszCmdLine[0])
        parent_pid = (DWORD)atol(lpszCmdLine);

    if (parent_pid)
        parent_proc = OpenProcess(SYNCHRONIZE, FALSE, parent_pid);

    if (!start_hook()) {
        if (parent_proc) CloseHandle(parent_proc);
        return;
    }

    /* Block until Python signals exit OR parent process dies */
    while (g_shm && g_shm->running) {
        if (parent_proc) {
            if (WaitForSingleObject(parent_proc, 100) != WAIT_TIMEOUT)
                break;  /* parent died */
        } else {
            Sleep(100);
        }
    }

    if (parent_proc)
        CloseHandle(parent_proc);

    stop_hook();
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH) {
        g_dll_module = hModule;
        DisableThreadLibraryCalls(hModule);
    }
    else if (reason == DLL_PROCESS_DETACH) {
        stop_hook();
    }
    return TRUE;
}
