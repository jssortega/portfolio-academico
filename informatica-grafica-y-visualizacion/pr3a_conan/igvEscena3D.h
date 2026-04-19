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
 * Los objetos de esta clase representan escenas 3D para su visualización
 */
class igvEscena3D
{  private:
      // Atributos
      bool ejes = true;   ///< Indica si hay que dibujar los _ejes coordenados o no

      // TODO: Apartado A: Añadir aquí los atributos con los ángulos de rotación en X, Y y Z.

      igvMallaTriangulos *malla = nullptr; ///< Malla de triángulos asociada a la escena

      float anguloX = 0;
      float anguloY = 0;
      float anguloZ = 0;

   public:
      // Constructores por defecto y destructor
      igvEscena3D ();
      ~igvEscena3D ();

      // Métodos
      // método con las llamadas OpenGL para visualizar la escena
      void visualizar ();

      bool get_ejes ();

      void set_ejes ( bool _ejes );

      // TODO: Apartado A: métodos para incrementar los ángulos
      // TODO: Apartado A: métodos para obtener los valores de los ángulos
      void setAnguloX(float anguloX);

    void setAnguloY(float anguloY);

    void setAnguloZ(float anguloZ);

    float getAnguloX() const;

    float getAnguloY() const;

    float getAnguloZ() const;

private:
      void pintar_ejes ();
};

#endif   // __IGVESCENA3D
