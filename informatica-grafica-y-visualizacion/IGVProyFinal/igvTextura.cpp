#include "igvTextura.h"
#include "lodepng.h"

#include <vector>
#include <stdexcept>
#include <iostream>

// Métodos constructores y destructor

/**
 * Constructor parametrizado. Carga una textura de archivo
 * @param fichero
 */
igvTextura::igvTextura ( std::string fichero )
{  glGenTextures(1, &idTextura);
    glBindTexture(GL_TEXTURE_2D, idTextura);

    // Configurar parámetros de la textura (puedes ajustar según tus necesidades)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // Cargar la textura desde el archivo
    std::vector<unsigned char> image; // Almacena la imagen cargada
    unsigned width, height;

    // Cargar la imagen usando lodepng
    unsigned error = lodepng::decode(image, width, height, fichero);

    // Verificar errores
    if (error) {
        std::cerr << "Error al cargar la imagen desde el archivo: " << lodepng_error_text(error) << std::endl;
        return;
    }

    // Asignar la textura a OpenGL
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image.data());

    // Asignar las dimensiones de la textura
    ancho = static_cast<unsigned int>(width);
    alto = static_cast<unsigned int>(height);
}

/**
 * Destructor. Elimina la textura OpenGL relacionada
 */
igvTextura::~igvTextura ()
{  glDeleteTextures ( 1, &idTextura );
}

/**
 * Activa la textura OpenGL relacionada
 */
void igvTextura::aplicar ()
{  glBindTexture ( GL_TEXTURE_2D, idTextura );
}

