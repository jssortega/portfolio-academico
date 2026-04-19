#ifndef __IGVCAJA
#define __IGVCAJA

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

/**
 * Los objetos de esta clase representan cajas en 3D
 */
class igvCaja
{  private:
      float color[3] = { 0, 0, 0 };   ///< Color RGB de la caja (valores [0..1])
      GLubyte colorUByte[3] = { 0, 0, 0 };   ///< Color RGB de la caja (valores [0..255])
    float rotationAngleX;  // Nueva variable para almacenar la rotación actual
    float rotationAngleY;  // Nueva variable para almacenar la rotación actual
    float totalX;

public:
      //Constructores y destructores
      /// Constructor por defecto
      igvCaja () = default;
      igvCaja ( float r, float g, float b );
      igvCaja ( const igvCaja &orig );
      ~igvCaja () = default;

      //M�todo para visualizar una caja
      void visualizar ();

      //Devuelve el color
      float *getColor ();
      GLubyte *getColorByte (); //Para comparar con el pixel obtenido en la selecci�n

      void setColor(float cl[]);

    void rotate(float angleX, float angleY);
    float getRotationAngle() const;


};

#endif   // __IGVCAJA
