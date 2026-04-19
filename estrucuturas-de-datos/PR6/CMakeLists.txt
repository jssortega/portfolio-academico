cmake_minimum_required(VERSION 3.23)
project(imagenes)

set(CMAKE_CXX_STANDARD 20)

add_executable(imagenes main.cpp fecha.cpp Imagen.cpp Imagen.h Timer.cpp ImageBook.cpp Usuario.cpp Etiqueta.cpp UTM.cpp MallaRegular.h
        )
