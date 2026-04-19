#include "igvCaja.h"
#include <iostream>

/**
 * Constructor parametrizado
 * @param r Valor de la componente roja (valor v�lido entre 0 y 1)
 * @param g Valor de la componente verde (valor v�lido entre 0 y 1)
 * @param b Valor de la componente azul (valor v�lido entre 0 y 1)
 * @pre Se asume que los tres par�metros tienen valores v�lidos
 * @post Los valores de color de la caja cambian
 */
igvCaja::igvCaja ( float r, float g, float b ): color { r, g, b }
{  colorUByte[0] = (GLubyte) ( color[0] * 255 );
   colorUByte[1] = (GLubyte) ( color[1] * 255 );
   colorUByte[2] = (GLubyte) ( color[2] * 255 );
};

/**
 * Constructor de copia
 * @param orig Caja de la que copia los datos
 * @post La nueva caja tiene una copia exacta de los atributos de la original
 */
igvCaja::igvCaja ( const igvCaja &orig ) : color { orig.color[0], orig.color[1]
                                                   , orig.color[2] }
                                         , colorUByte { orig.colorUByte[0]
                                                        , orig.colorUByte[1]
                                                        , orig.colorUByte[2] }
{ }

/**
 * M�todo para visualizar una caja llamando a funciones de OpenGL
 */
void igvCaja::visualizar ()
{  glMaterialfv ( GL_FRONT, GL_EMISSION, color );
   glColor3fv ( color );//Importante, es necesario para que lo reconozca el buffer de color a la hora de la selecci�n.
totalX += rotationAngleX;
   glPushMatrix ();
    glRotatef(totalX, 0.0f, 1.0f, 0.0f);
    glRotatef(rotationAngleY, 0.0f, 1.0f, 0.0f);
   glScalef ( 1, 1, 2 );
   glutSolidCube ( 1 );
   glPopMatrix ();

   glPushMatrix ();
    glRotatef(totalX, 0.0f, 1.0f, 0.0f);
    glRotatef(rotationAngleY, 0.0f, 1.0f, 0.0f);
   glTranslatef ( 0, 0.4, 0 );
   glScalef ( 1.1, 0.2, 2.1 );
   glutSolidCube ( 1 );
   glPopMatrix ();
};

/**
 * Consulta el color de la caja
 * @return La direcci�n de memoria del bloque de tres valores con el color RGB
 *         de la caja
 */
float *igvCaja::getColor ()
{  return color;
}

/**
 * Consulta el color de la caja
 * @return La direcci�n de memoria del bloque de tres valores con el color RGB
 *         de la caja
 */
GLubyte *igvCaja::getColorByte ()
{  return colorUByte;
}

void igvCaja::setColor(float *cl) {
    color[0] = cl[0];
    color[1] = cl[1];
    color[2] = cl[2];
}
void igvCaja::rotate(float angleX, float angleY) {
rotationAngleX=angleX;
rotationAngleY=angleY;
}


