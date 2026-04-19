#include <cstdlib>
#include <stdio.h>
#include <iostream>

#include "igvEscena3D.h"
#include "igvTextura.h"

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
 * M�todo para pintar un cuadril�tero en la escena
 */
void igvEscena3D::pintar_quad (int div_x, int div_z)
{  float ini_x = 0.0;
    float ini_z = 0.0;
    float tam_x = 5.0;
    float tam_z = 5.0;

    glBegin(GL_QUADS);
    for (int i = 0; i < div_x; ++i) {
        for (int j = 0; j < div_z; ++j) {
            float x0 = ini_x + i * (tam_x / div_x);
            float z0 = ini_z + j * (tam_z / div_z);
            float x1 = x0 + (tam_x / div_x);
            float z1 = z0 + (tam_z / div_z);

            // Coordenadas de textura
            float s0 = i / static_cast<float>(div_x);
            float t0 = j / static_cast<float>(div_z);
            float s1 = (i + 1) / static_cast<float>(div_x);
            float t1 = (j + 1) / static_cast<float>(div_z);

            glTexCoord2f(s0, t0);
            glVertex3f(x0, 0.0, z0);

            glTexCoord2f(s0, t1);
            glVertex3f(x0, 0.0, z1);

            glTexCoord2f(s1, t1);
            glVertex3f(x1, 0.0, z1);

            glTexCoord2f(s1, t0);
            glVertex3f(x1, 0.0, z0);
        }
    }
    glEnd();
}

// M�todos p�blicos

/**
 * M�todo con las llamadas OpenGL para visualizar la escena
 */
void igvEscena3D::visualizar ()
{  // crear el modelo
   glPushMatrix (); // guarda la matriz de modelado

   if ( ejes )
   {  pintar_ejes (); // se pintan los ejes
   }

   // luces se aplican antes de las transformaciones a la escena para que permanezcan fijas

   // TODO: APARTADO A: Define y aplica la luz puntual especificada en el gui�n de pr�cticas
    igvPunto3D posicion(1.0, 1.0, 1.0);
    igvColor colorAmbiental(0.0, 0.0, 1.0);
   igvColor colorDifuso(1.0, 1.0, 1.0);
    igvColor colorEspecular(1.0, 1.0, 1.0);

    luz.setPosicion(posicion);
    luz.setAmbiental(colorAmbiental);
    luz.setDifuso(colorDifuso);
    luz.setEspecular(colorEspecular);
    luz.setAtenuacion(1,0,0);
    luz.encender();
   // TODO: APARTADO E: Define y aplica la luz tipo foco especificada en el gui�n de pr�cticas


   /* TODO: Apartado B: definir y aplicar las propiedades de material indicadas en el gui�n de pr�cticas */

   /* TODO: Apartado D: sustituir los valores correspondientes a la componente R del coeficiende difuso,
                  la componente R del coeficiente especular y el exponente de Phong, por el valor
                         del atributo correspondiente de la clase igvEscena */
   igvColor kd(coefDifusoR,material.getKd()[1],material.getKd()[2]);
   igvColor ks(coefEspecularR,material.getKs()[1],material.getKs()[2]);
   material.set(material.getKa(),kd,ks,expPhong);

   /* TODO: Apartado F: A�ade aqu� la creaci�n del objeto textura y su aplicaci�n */
    igvTextura textura("/home/jortega/CLionProjects/pr4_conan/map.png");
    textura.aplicar();
    glEnable(GL_TEXTURE_2D);
   pintar_quad (50,50);

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

void igvEscena3D::setCoefDifusoR(float coefDifusoR) {
    igvEscena3D::coefDifusoR = coefDifusoR;
}

void igvEscena3D::setCoefEspecularR(float coefEspecularR) {
    igvEscena3D::coefEspecularR = coefEspecularR;
}

void igvEscena3D::setExpPhong(float expPhong) {
    igvEscena3D::expPhong = expPhong;
}

float igvEscena3D::getCoefDifusoR() const {
    return coefDifusoR;
}

float igvEscena3D::getCoefEspecularR() const {
    return coefEspecularR;
}

float igvEscena3D::getExpPhong() const {
    return expPhong;
}
