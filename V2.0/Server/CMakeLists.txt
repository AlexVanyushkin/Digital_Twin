cmake_minimum_required(VERSION 3.14) #показывает какой минимальной версией можно собрать проект

project(server) #дает имя проекту




# Позволяем CMake найти библиотеки vcpkg, если переменная не задана
#if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    # set(CMAKE_TOOLCHAIN_FILE "/home/user/vcpkg/scripts/buildsystems/vcpkg.cmake" CACHE STRING "")
#endif()
set(CMAKE_TOOLCHAIN_FILE "C:/vcpkg/scripts/buildsystems/vcpkg.cmake" CACHE STRING "")
set(CMAKE_CXX_STANDARD 17)


#дает понять что будет собираться исполняемый файл(exe)
#первый аргумент - это название собираемоего проекта, остальные исходные файлы *.h *.cpp
#все аргументы записываются через пробел
add_executable(main src/main.cpp) 