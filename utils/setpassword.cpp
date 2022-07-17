#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <cstring>
#include <string>
#include <pwd.h>

int main(int argc, char *argv[]) {
    // If --debug is in argv, set the debug flag to true.
    bool debug = false;
    if (argc > 1 && strcmp(argv[1], "--debug") == 0) {
        debug = true;
    }

    int uid = getuid();
    struct passwd *pws;
    pws = getpwuid(uid);

    if (debug) 
        std::cout << "geteuid(): " << geteuid() << " getuid(): " << getuid() << " username: " << pws->pw_name << std::endl;

    char cmd[128] = "/bin/python3 /bin/setpassword.py ";
    std::strcat(cmd, pws->pw_name);

    setuid(0);
    return std::system(cmd);
}