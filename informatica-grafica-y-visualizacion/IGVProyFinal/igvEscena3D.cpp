#include <cstdlib>
#include <stdio.h>
#include <cmath>
#include "iostream"

#include "igvEscena3D.h"
#include "igvMallaTriangulos.h"
#include "igvFigura.h"


// M�todos constructores

/**
 * Constructor por defecto
 */
igvEscena3D::igvEscena3D ()
{  ///< creamos un cilindro y un cuadrado
    igvFigura cilindro(0.05, 0.7, 40, 2,0);
    igvFigura cuadrado(1,1,40,2);
    mallaCilindro = new igvMallaTriangulos(cilindro.getNumVerticesCilindro() / 3, cilindro.getVerticesCilindro(),
                                           cilindro.getNumTriangulosCilindro() / 3, cilindro.getTriangulosCilindro());
    mallaCuadrado = new igvMallaTriangulos(cuadrado.getNumVerticesCuadrado() / 3, cuadrado.getVerticesCuadrado(),
                                           cuadrado.getNumTriangulosCuadrado() / 3, cuadrado.getTriangulosCuadrado());
}

/**
 * Destructor
 */
igvEscena3D::~igvEscena3D ()
{  if ( mallaCilindro != nullptr )
   {  delete mallaCilindro;
      mallaCilindro = nullptr;
   }
    if ( mallaCuadrado != nullptr )
    {  delete mallaCuadrado;
        mallaCuadrado = nullptr;
    }
}


// M�todos p�blicos

/**
 * M�todo para pintar los ejes coordenados llamando a funciones de OpenGL
 */
void igvEscena3D::pintar_ejes()
{	GLfloat rojo[] = { 1,0,0,1.0 };
   GLfloat verde[] = { 0,1,0,1.0 };
   GLfloat azul[] = { 0,0,1,1.0 };

   glMaterialfv(GL_FRONT, GL_EMISSION, rojo);
   glBegin(GL_LINES);
   glVertex3f(1000, 0, 0);
   glVertex3f(-1000, 0, 0);
   glEnd();

   glMaterialfv(GL_FRONT, GL_EMISSION, verde);
   glBegin(GL_LINES);
   glVertex3f(0, 1000, 0);
   glVertex3f(0, -1000, 0);
   glEnd();

   glMaterialfv(GL_FRONT, GL_EMISSION, azul);
   glBegin(GL_LINES);
   glVertex3f(0, 0, 1000);
   glVertex3f(0, 0, -1000);
   glEnd();
}

/**
 * M�todo con las llamadas OpenGL para visualizar la escena
 */
void igvEscena3D::visualizar ( void )
{  GLfloat color_malla[] = { 0, 0.25, 0 };
   // crear luces
   // luz puntual para visualizar el cubo
   GLfloat luz0[4] = { 2.0, 2.5, 3.0, 1 };

   // la luz se coloca aqu� si permanece fija y no se mueve con la escena
   glLightfv ( GL_LIGHT0, GL_POSITION, luz0 );
   glEnable ( GL_LIGHT0 );

   // crear el modelo
   glPushMatrix (); // guarda la matriz de modelado

   // se pintan los ejes
   if ( ejes )
   {  pintar_ejes ();
   }

   // la luz se coloca aqu� si se mueve junto con la escena
   //glLightfv(GL_LIGHT0,GL_POSITION,luz0);
   glMaterialfv ( GL_FRONT, GL_EMISSION, color_malla );

   mallaCuadrado->visualizar(mallaCuadrado, mallaCilindro);

   glPopMatrix (); // restaura la matriz de modelado
}

/**
 * M�todo para consultar si hay que dibujar los ejes o no
 * @retval true Si hay que dibujar los ejes
 * @retval false Si no hay que dibujar los ejes
 */
bool igvEscena3D::get_ejes ()
{  return ejes;
}

/**
 * M�todo para activar o desactivar el dibujado de los _ejes
 * @param _ejes Indica si hay que dibujar los ejes (true) o no (false)
 * @post El estado del objeto cambia en lo que respecta al dibujado de ejes,
 *       de acuerdo al valor pasado como par�metro
 */
void igvEscena3D::set_ejes ( bool _ejes )
{  ejes = _ejes;
}

igvMallaTriangulos *igvEscena3D::getMallaCuadrado() const {
    return mallaCuadrado;
}

igvMallaTriangulos *igvEscena3D::getMallaCilindro() const {
    return mallaCilindro;
}


