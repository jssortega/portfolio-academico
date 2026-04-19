#ifndef __IGVMATERIAL
#define __IGVMATERIAL

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

#include "igvColor.h"

/**
 * Los objetos de esta clase representan propiedades de material
 */
class igvMaterial
{  private:
      // atributos
      igvColor Ka = { 0, 0, 0 }; ///< Coeficiente de reflexi�n ambiental
      igvColor Kd = { 0, 0, 0 }; ///< Coeficiente de reflexi�n difuso
      igvColor Ks = { 0, 0, 0 }; ///< Coeficiente de reflexi�n especular
      double Ns = 0; ///< Exponente de Phong

      // M�todos

   public:
      // Constructores por defecto y destructor
      /// Constructor por defecto
      igvMaterial () = default;
      /// Destructor
      ~igvMaterial () = default;

      // Otros constructores
      igvMaterial ( const igvMaterial &p );   //de copia
      igvMaterial ( igvColor _Ka, igvColor _Kd, igvColor _Ks, double _Ns );

      // M�todos
      void aplicar ();

      void set ( igvColor _Ka, igvColor _Kd, igvColor _Ks, double _Ns );

    const igvColor &getKa() const;

    const igvColor &getKd() const;

    const igvColor &getKs() const;

    double getNs() const;
};

#endif   // __IGVMATERIAL

