cmake_minimum_required(VERSION 3.25)
project(pr4)

set(CMAKE_CXX_STANDARD 14)

include_directories(.)

add_executable(${PROJECT_NAME}
        igvCamara.cpp
        igvCamara.h
        igvColor.cpp
        igvColor.h
        igvEscena3D.cpp
        igvEscena3D.h
        igvFuenteLuz.cpp
        igvFuenteLuz.h
        igvInterfaz.cpp
        igvInterfaz.h
        igvMaterial.cpp
        igvMaterial.h
        igvPunto3D.cpp
        igvPunto3D.h
        igvTextura.cpp
        igvTextura.h
        lodepng.cpp
        lodepng.h
        pr4.cpp)

if (LINUX)
    find_path(OPENGL_REGISTRY_INCLUDE_DIRS "GL/glcorearb.h")
    target_include_directories(${PROJECT_NAME} PRIVATE ${OPENGL_REGISTRY_INCLUDE_DIRS})

    find_package(OpenGL REQUIRED)
    target_link_libraries(${PROJECT_NAME} PRIVATE ${OPENGL_LIBRARIES})
    target_include_directories(${PROJECT_NAME} PRIVATE ${OPENGL_INCLUDE_DIR})

    find_package(GLUT REQUIRED)
    target_link_libraries(${PROJECT_NAME} PRIVATE GLUT::GLUT)
endif ()

if (WIN32)
    find_package(opengl_system)
    target_link_libraries(${PROJECT_NAME} opengl::opengl)

    find_package(opengl-registry)
    target_link_libraries(${PROJECT_NAME} opengl-registry::opengl-registry)

    find_package(FreeGLUT)
    target_link_libraries(${PROJECT_NAME} FreeGLUT::freeglut_static)
endif ()
