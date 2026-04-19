#ifndef __IGV_CILINDRO
#define __IGV_CILINDRO

#include "vector"
#include "igvMallaTriangulos.h"

/**
 * Los objetos de esta clase representan cilindros en 3D sin las tapas superior
 * e inferior
 */
class igvCilindro : public igvMallaTriangulos
{  public:
      // Constructores y destructor
      igvCilindro ();
      igvCilindro ( float r, float a, int divU, int divV );
      ~igvCilindro ();

};

#endif   // __IGV_CILINDRO