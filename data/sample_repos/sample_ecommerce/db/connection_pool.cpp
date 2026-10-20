#include <iostream>
#include <string>
#include <vector>

class ConnectionPool {
private:
    int maxConnections;
    int activeConnections;

public:
    ConnectionPool(int maxConn = 10) : maxConnections(maxConn), activeConnections(0) {}

    int acquire() {
        if (activeConnections >= maxConnections) {
            std::cout << "Pool exhausted" << std::endl;
            return -1;
        }
        activeConnections++;
        return activeConnections;
    }

    void release(int connId) {
        if (activeConnections > 0) {
            activeConnections--;
        }
    }
};
