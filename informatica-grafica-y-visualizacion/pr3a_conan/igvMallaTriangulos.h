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

/**
 * Los objetos de esta clase representan mallas de triángulos
 */
class igvMallaTriangulos
{  protected:
      // Atributos
      long int num_vertices = 0; ///< Número de vértices de la malla de triángulos
      float *vertices = nullptr; ///< Array con las (num_vertices * 3) coordenadas de los vértices
      float *normales = nullptr; ///< Array con las (num_vertices * 3) coordenadas de la normal en cada vértice (sólo para la generación de la esfera)

      long int num_triangulos = 0; ///< Número de triángulos de la malla de triángulos
      unsigned int *triangulos = nullptr; ///< Array con los (num_triangulos * 3) índices a los vértices de cada triángulo


   public:
      // Constructor y destructor
      /// Constructor por defecto
      igvMallaTriangulos () = default;

      igvMallaTriangulos ( long int _num_vertices, float *_vertices
                           , long int _num_triangulos, unsigned int *_triangulos );

      ~igvMallaTriangulos ();

      // Método con las llamadas OpenGL para visualizar la malla de triángulos
      void visualizar ( igvMallaTriangulos *malla);

    long getNumVertices() const;

    float *getVertices() const;

    float *getNormales() const;

    long getNumTriangulos() const;

    unsigned int *getTriangulos() const;
};

#endif   // __IGVMALLATRIANGULOS
