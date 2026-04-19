#ifndef __IGVESCENA3D
#define __IGVESCENA3D

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif // defined(__APPLE__) && defined(__MACH__)

#include "igvMallaTriangulos.h"

/**
 * Los objetos de esta clase representan escenas 3D para su visualizaci�n
 */
class igvEscena3D
{  private:
      // Atributos
      bool ejes = true;   ///< Indica si hay que dibujar los _ejes coordenados o no

      ///< Crea las dos mallas, la de cilindro y las caras
      igvMallaTriangulos *mallaCuadrado = nullptr; ///< Malla de tri�ngulos asociada a la escena
      igvMallaTriangulos *mallaCilindro = nullptr; ///< Malla de tri�ngulos asociada a la escena

   public:
      // Constructores por defecto y destructor
      igvEscena3D ();
      ~igvEscena3D ();

      // Metodos
      // metodo con las llamadas OpenGL para visualizar la escena
      void visualizar ();

      bool get_ejes ();

      void set_ejes ( bool _ejes );

    igvMallaTriangulos *getMallaCuadrado() const;

    igvMallaTriangulos *getMallaCilindro() const;

private:
      void pintar_ejes ();
};

#endif   // __IGVESCENA3D
