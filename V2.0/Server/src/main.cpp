#include <cstdlib>
#include <iostream>
#include <drogon/drogon.h>

using namespace drogon;

int main() {
    std::cout << "Running server on 0.0.0.0:3000...";
    app()
        .loadConfigFile("./config.json")
        .run();
    
    return EXIT_SUCCESS;
}