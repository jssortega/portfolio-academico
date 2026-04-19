#ifndef __IGVESCENA3D
#define __IGVESCENA3D

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif // defined(__APPLE__) && defined(__MACH__)

#include <vector>
#include "igvCaja.h"

/**
 * Los objetos de esta clase representan escenas 3D para su visualizaci�n
 */
class igvEscena3D
{  private:
      bool ejes = true;   ///< Indica si hay que dibujar los ejes coordenados o no
      std::vector<igvCaja *> cajas; ///< Vector con todos los objetos de la escena
   public:

      // Constructores por defecto y destructor
      igvEscena3D ();
      ~igvEscena3D ();

      // m�todo con las llamadas OpenGL para visualizar la escena
      void visualizar ();
      void visualizarVB ();

      bool get_ejes ();

      void set_ejes ( bool _ejes );

      std::vector<igvCaja *> &getCajas ();

   private:
      void pintar_ejes ();

public:

};

#endif   // __IGVESCENA3D
