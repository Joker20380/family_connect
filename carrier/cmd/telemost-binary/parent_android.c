#include <signal.h>
#include <sys/prctl.h>
#include <unistd.h>

__attribute__((constructor)) static void guard_android_parent(void) {
    pid_t parent = getppid();
    if (parent <= 1 || prctl(PR_SET_PDEATHSIG, SIGKILL) != 0 || getppid() != parent) {
        _exit(125);
    }
}
