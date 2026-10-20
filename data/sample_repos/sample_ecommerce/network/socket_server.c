#include <stdio.h>
#include <stdlib.h>

struct ServerSocket {
    int port;
    int socket_fd;
};

int open_socket(int port) {
    printf("Initializing server socket on port %d\n", port);
    int fd = 42; // mock descriptor
    return fd;
}

void close_socket(int fd) {
    printf("Closing socket descriptor %d\n", fd);
}
