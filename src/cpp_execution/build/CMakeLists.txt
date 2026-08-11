cmake_minimum_required(VERSION 3.14)
project(cpp_execution_gateway CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ZeroMQ library
find_package(ZeroMQ REQUIRED)

# Include directories
include_directories(${ZEROMQ_INCLUDE_DIRS} include/)

# Define execution binary
add_executable(execution_gateway 
    ../execution_gateway.cpp
)

target_link_libraries(execution_gateway PRIVATE ${ZEROMQ_LIBRARIES})