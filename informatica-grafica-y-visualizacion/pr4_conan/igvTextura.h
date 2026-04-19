#ifndef __IGVTEXTURA
#define __IGVTEXTURA

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

#include <string>

/**
 * Los objetos de esta clase representan texturas OpenGL
 */
class igvTextura
{  private:
      // Atributos
      unsigned int idTextura = 0; ///< Identificador de la textura OpenGL
      unsigned int alto = 0  ///< Alto de la textura
                   , ancho = 0; ///< Ancho de la textura

      // Métodos

   public:
      // Constructores por defecto y destructor
      /// Constructor por defecto
      igvTextura () = default;
      igvTextura ( std::string fichero ); // Textura cargada desde un fichero
      ~igvTextura ();

      // Métodos
      void aplicar (); //Establece la textura como la activa
      void setIdTextura ( unsigned int id );

      unsigned int getIdTextura ();
};

#endif   // __IGVTEXTURA

