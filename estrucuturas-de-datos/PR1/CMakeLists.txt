cmake_minimum_required(VERSION 3.22.3)
project(imagenes)

set(CMAKE_CXX_STANDARD 20)

add_executable(imagenes main.cpp fecha.cpp Imagen.cpp Imagen.h ContenedorImagenes.cpp ContenedorImagenes.h Timer.cpp VDinamico.h)
