#ifndef __IGV_CILINDRO
#define __IGV_CILINDRO

#include "vector"
#include "igvMallaTriangulos.h"

/**
 * Los objetos de esta clase representan cilindros en 3D sin las tapas superior
 * e inferior
 */
class igvFigura : public igvMallaTriangulos
{  public:
      // Constructores y destructor
      igvFigura ();
      igvFigura(float r, float a, int divU, int divV,int nada );
      igvFigura(double l, float a, int divU, int divV );
      ~igvFigura ();

};

#endif   // __IGV_CILINDRO