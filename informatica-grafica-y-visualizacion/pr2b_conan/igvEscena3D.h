#ifndef __IGVESCENA3D
#define __IGVESCENA3D

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

/**
 * Los objetos de esta clase representan escenas 3D para su visualización
 */
class igvEscena3D
{  private:
      // Atributos
      bool ejes = true;   ///< Indica si hay que dibujar los _ejes coordenados o no

   public:
      // Constructores por defecto y destructor
      /// Constructor por defecto
      igvEscena3D () = default;
      /// Destructor
      ~igvEscena3D () = default;

      // Métodos
      // método con las llamadas OpenGL para visualizar la escena
      void visualizar ();

      bool get_ejes ();

      void set_ejes ( bool _ejes );

   private:
      void pintar_tubo ();
      void pintar_ejes ();
};

#endif   // __IGVESCENA3D
