#ifndef __IGVCAMARA
#define __IGVCAMARA

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

#include "igvPunto3D.h"

/**
 * Etiquetas para los diferentes tipos de c�mara
 */
enum tipoCamara
{  IGV_PARALELA   ///< Proyecci�n paralela
   , IGV_FRUSTUM   ///< Proyecci�n en perspectiva usando OpenGL
   , IGV_PERSPECTIVA   ///< Proyecci�n en perspectiva usando GLU
};

/**
 * Los objetos de esta clase representan c�maras de visualizaci�n en la aplicaci�n
 */
class igvCamara
{  private:
      // atributos
      tipoCamara tipo = IGV_PARALELA;  ///< Tipo de la c�mara

      // ventana de visi�n: par�metros proyecci�n paralela y frustum
      GLdouble xwmin = -3    ///< Coordenada X m�nima del frustum/proyecci�n paralela
               , xwmax = 3   ///< Coordenada X m�xima del frustum/proyecci�n paralela
               , ywmin = -3   ///< Coordenada Y m�nima del frustum/proyecci�n paralela
               , ywmax = 3   ///< Coordenada Y m�xima del frustum/proyecci�n paralela
               ;

      // ventana de visi�n: par�metros proyecci�n perspectiva
      GLdouble angulo = 60   ///< �ngulo de apertura (proyecci�n perspectiva)
               , raspecto = 1   ///< Raz�n de aspecto (proyecci�n perspectiva)
               ;

      // distancias de planos cercano y lejano
      GLdouble znear = 1    ///< Distancia de la c�mara al plano Z near
               , zfar = 200 ///< Distancia de la c�mara al plano Z far
               ;

      // punto de visi�n
      igvPunto3D P0 = { 3, 2, 4 };   ///< Posici�n de la c�mara

      // punto de referencia de visi�n
      igvPunto3D r = { 0, 0, 0 };   ///< Punto al que mira la c�mara

      // vector arriba
      igvPunto3D V = { 0, 1, 0 };   ///< Vector que indica la vertical

      // M�todos

   public:
      // Constructores por defecto y destructor
      /// Constructor por defecto
      igvCamara () = default;

      /// Destructor
      ~igvCamara () = default;

      // Otros constructores
      igvCamara ( tipoCamara _tipo, igvPunto3D _P0, igvPunto3D _r, igvPunto3D _V );

      // M�todos
      // define la posici�n de la c�mara
      void set ( igvPunto3D _P0, igvPunto3D _r, igvPunto3D _V );

      // define una c�mara de tipo paralela o frustum
      void set ( tipoCamara _tipo, igvPunto3D _P0, igvPunto3D _r, igvPunto3D _V
                 , double _xwmin, double _xwmax, double _ywmin
                 , double _ywmax, double _znear, double _zfar );

      // define una c�mara de tipo perspectiva
      void set ( tipoCamara _tipo, igvPunto3D _P0, igvPunto3D _r, igvPunto3D _V
                 , double _angulo, double _raspecto, double _znear, double _zfar );

      void aplicar ( void ); // aplica a los objetos de la escena la transformaci�n
                             // de visi�n y la transformaci�n de proyecci�n
                             // asociadas a los par�metros de la c�mara
      void zoom ( double factor ); // realiza un zoom sobre la c�mara

};

#endif   // __IGVCAMARA

