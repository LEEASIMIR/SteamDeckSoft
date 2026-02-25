/*
 * numpad_launcher.exe — thin launcher that loads numpad_hook.dll
 * in a separate process.
 *
 * The DLL contains the actual WH_KEYBOARD_LL hook callback (which
 * MUST be in a DLL for Windows to deliver callbacks).
 *
 * Compile:
 *   gcc -O2 -mwindows -o numpad_launcher.exe numpad_launcher.c -lkernel32
 */

#include <windows.h>

typedef int  (__cdecl *start_hook_fn)(void);
typedef void (__cdecl *stop_hook_fn)(void);

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow)
{
    /* Load the DLL from the same directory as this exe */
    wchar_t path[MAX_PATH];
    GetModuleFileNameW(NULL, path, MAX_PATH);

    /* Replace exe name with dll name */
    wchar_t *slash = wcsrchr(path, L'\\');
    if (slash) slash[1] = 0;
    else       path[0] = 0;
    wcscat(path, L"numpad_hook.dll");

    HMODULE dll = LoadLibraryW(path);
    if (!dll) return 1;

    start_hook_fn start = (start_hook_fn)GetProcAddress(dll, "start_hook");
    stop_hook_fn  stop  = (stop_hook_fn)GetProcAddress(dll, "stop_hook");
    if (!start || !stop) return 2;

    if (!start()) return 3;

    /* Keep alive — the DLL's hook thread does all the work.
       Sleep until the process is terminated externally. */
    Sleep(INFINITE);

    stop();
    FreeLibrary(dll);
    return 0;
}
