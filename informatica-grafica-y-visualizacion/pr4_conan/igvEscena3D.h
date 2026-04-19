#ifndef __IGVESCENA3D
#define __IGVESCENA3D

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>
#include "igvFuenteLuz.h"
#include "igvMaterial.h"

#endif // defined(__APPLE__) && defined(__MACH__)


/**
 * Los objetos de esta clase representan escenas 3D para su visualización
 */
class igvEscena3D
{  private:
      // Atributos

      bool ejes = true;   ///< Indica si hay que dibujar los ejes coordenados o no

      igvFuenteLuz luz;

      igvMaterial material;

    float coefDifusoR = 1.0;    // Componente R del coeficiente difuso
    float coefEspecularR = 1.0; // Componente R del coeficiente especular
    float expPhong = 50.0;      // Exponente de Phong
   public:

      // Constructores por defecto y destructor
      igvEscena3D () = default;
      ~igvEscena3D () = default;

      // Métodos
      // método con las llamadas OpenGL para visualizar la escena
      void visualizar ();

      bool get_ejes ();

      void set_ejes ( bool _ejes );

    void setCoefDifusoR(float coefDifusoR);

    void setCoefEspecularR(float coefEspecularR);

    void setExpPhong(float expPhong);

    float getCoefDifusoR() const;

    float getCoefEspecularR() const;

    float getExpPhong() const;

private:
      void pintar_ejes ();
      void pintar_quad (int div_x, int div_z);
};

#endif   // __IGVESCENA3D
