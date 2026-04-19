#include <cstdlib>
#include <stdio.h>
#include <iostream>
#include "igvEscena3D.h"

// M�todos constructores

/**
 * Constructor por defecto
 */

constexpr int FLOAT_MIN = 0;
constexpr int FLOAT_MAX = 1;

igvEscena3D::igvEscena3D ()
{
    for ( int pilasY = 0 ; pilasY < 3; pilasY++ )
    {  for ( int pilasX = 0 ; pilasX < 3; pilasX++ )
        {  for ( int pilasZ = 0 ; pilasZ < 3 ; pilasZ++ )
            {  cajas.push_back ( new igvCaja ( FLOAT_MIN+(float)(rand())/((float)(RAND_MAX/(FLOAT_MAX-FLOAT_MIN))), FLOAT_MIN+(float)(rand())/((float)(RAND_MAX/(FLOAT_MAX-FLOAT_MIN))), FLOAT_MIN+(float)(rand())/((float)(RAND_MAX/(FLOAT_MAX-FLOAT_MIN))) ) ); //Se crea una nueva caja con el color indicado
            }
        }
    }
}

/**
 * Destructor
 */
igvEscena3D::~igvEscena3D ()
{  while ( cajas.size() > 0 )
   {  delete cajas.back();
      cajas.back() = nullptr;
      cajas.pop_back();
   }
}

/**
 * M�todo para pintar los ejes coordenados llamando a funciones de OpenGL
 */
void igvEscena3D::pintar_ejes()
{	GLfloat rojo[] = { 1,0,0,1.0 };
   GLfloat verde[] = { 0, 1, 0, 1.0 };
   GLfloat azul[] = { 0, 0, 1, 1.0 };

   glMaterialfv ( GL_FRONT, GL_EMISSION, rojo );
   glBegin ( GL_LINES );
   glVertex3f ( 1000, 0, 0 );
   glVertex3f ( -1000, 0, 0 );
   glEnd ();

   glMaterialfv ( GL_FRONT, GL_EMISSION, verde );
   glBegin ( GL_LINES );
   glVertex3f ( 0, 1000, 0 );
   glVertex3f ( 0, -1000, 0 );
   glEnd ();

   glMaterialfv ( GL_FRONT, GL_EMISSION, azul );
   glBegin ( GL_LINES );
   glVertex3f ( 0, 0, 1000 );
   glVertex3f ( 0, 0, -1000 );
   glEnd ();
}

/**
 * M�todo con las llamadas OpenGL para visualizar la escena
 */
void igvEscena3D::visualizar ()
{  // crear luces
   GLfloat luz0[4] = { 5.0, 5.0, 5.0, 1 }; // luz puntual
   glLightfv ( GL_LIGHT0, GL_POSITION, luz0 ); // la luz se coloca aqu� si permanece fija y no se mueve con la escena
   glEnable ( GL_LIGHT0 );

   // crear el modelo
   glPushMatrix (); // guarda la matriz de modelado
   if ( ejes )
   {  pintar_ejes (); // se pintan los ejes
   }
   glPopMatrix ();

   glPushMatrix ();
   visualizarVB ();
   glPopMatrix ();
}

/**
 * M�todo para la visualizaci�n del modelo sin luces (se utiliza durante la
 * selecci�n)
 */


void igvEscena3D::visualizarVB ()
{  GLfloat separacionX = 2.5;
   GLfloat separacionZ = 2.5;

   int cont = 0;
   // TODO: Practica 2a. Parte B y C.
   for ( int pilasY = 0 ; pilasY < 3 ; pilasY++ )
   {  for ( int pilasX = 0 ; pilasX < 3 ; pilasX++ )
      {  for ( int pilasZ = 0 ; pilasZ < 3 ; pilasZ++ )
         {  glPushMatrix ();
            glTranslatef ( pilasX * separacionX, pilasY, pilasZ * separacionZ );
            cajas[cont++]->visualizar(); //Se visualiza la caja
            glPopMatrix ();
         }
      }
   }
}

/**
 * Consulta las cajas
 * @return Una referencia al contenedor STL de las cajas
 */
std::vector<igvCaja*>& igvEscena3D::getCajas ()
{  return cajas;
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


