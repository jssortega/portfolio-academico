#ifndef __IGVMALLATRIANGULOS
#define __IGVMALLATRIANGULOS

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

#include <string>
#include "igvTextura.h"

/**
 * Los objetos de esta clase representan mallas de tri�ngulos
 */
class igvMallaTriangulos
{  protected:
      // Atributos
      long int num_verticesCuadrado = 0; ///< N�mero de v�rtices de la malla de tri�ngulos
    long int num_verticesCilindro = 0;

    float *verticesCilindro = nullptr;///< Array con las (num_verticesCuadrado * 3) coordenadas de los v�rtices
    float *verticesCuadrado = nullptr;

    long int num_triangulosCuadrado = 0; ///< N�mero de tri�ngulos de la malla de tri�ngulos
    long int num_triangulosCilindro = 0;

    unsigned int *triangulosCilindro = nullptr;///< Array con los (num_triangulosCuadrado * 3) �ndices a los v�rtices de cada tri�ngulo
    unsigned int *triangulosCuadrado = nullptr;

    // Angulo de rotación de las partes del cuerpo
    float angBrazoIzq = 0;
    float angBrazoDer = 0;
    float angPiernaIzq = 0;
    float angPiernaDer = 0;
    float angZapaIzq = 0;
    float angZapaDer = 0;

    // Movimiento del gorro
    float gorroY = 0;
    float gorroX = 0;

   public:
      // Constructor y destructor
      /// Constructor por defecto
      igvMallaTriangulos () = default;

      igvMallaTriangulos ( long int _num_vertices, float *_vertices
                           , long int _num_triangulos, unsigned int *_triangulos );

      ~igvMallaTriangulos ();

      // M�todo con las llamadas OpenGL para visualizar la malla de tri�ngulos
      void visualizar ( igvMallaTriangulos *malla, igvMallaTriangulos *malla2);

    long getNumVerticesCuadrado() const;
    long getNumVerticesCilindro() const;

    float *getVerticesCilindro() const;
    float *getVerticesCuadrado() const;

    long getNumTriangulosCuadrado() const;
    long getNumTriangulosCilindro() const;

    unsigned int *getTriangulosCilindro() const;
    unsigned int *getTriangulosCuadrado() const;

    // Métodos get y set de los atributos
     float getAngBrazoIzq() const;
     void setAngBrazoIzq(float angBrazoIzq);

    void setAngBrazoDer(float angBrazoDer);
    int getAngBrazoDer() const;

    int getAngPiernaIzq() const;
    int getAngPiernaDer() const;

    void setAngPiernaIzq(int angPiernaIzq);
    void setAngPiernaDer(int angPiernaDer);

    float getAngZapaIzq() const;
    void setAngZapaIzq(int angZapaIzq);

    float getAngZapaDer() const;
    void setAngZapaDer(int angZapaDer);

    float getGorroY() const;
    void setGorroY(float gorroY);

    float getGorroX() const;
    void setGorroX(float gorroX);
};

#endif   // __IGVMALLATRIANGULOS
