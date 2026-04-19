#include <cstdlib>
#include <stdio.h>

#include "igvEscena3D.h"

// M�todos constructores

/**
 * Constructor por defecto
 */
igvEscena3D::igvEscena3D ()
{  // TODO: Apartado C: inicializar los atributos para el control de los grados de libertad del modelo
}

/**
 * Destructor
 */
igvEscena3D::~igvEscena3D ()
{
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

// M�todos p�blicos

// TODO: Apartado B: M�todos para visualizar cada parte del modelo

// TODO: Apartado C: a�adir aqu� los m�todos para modificar los grados de libertad del modelo


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

   // se pintan los ejes
   if ( ejes )
   { pintar_ejes (); }

   //glLightfv(GL_LIGHT0,GL_POSITION,luz0); // la luz se coloca aqu� si se mueve junto con la escena (tambi�n habr�a que desactivar la de arriba).



   // TODO: Apartado B: aqu� hay que a�adir la visualizaci�n del �rbol del modelo utilizando la pila de matrices de OpenGL
   //       se recomienda crear una m�todo auxiliar que encapsule el c�digo para la visualizaci�n
   //       del modelo, dejando aqu� s�lo la llamada a ese m�todo, as� como distintas funciones una para cada
   //       parte del modelo.

   crearEscena();
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

float igvEscena3D::getCuerpo() const {
    return angCuerpo;
}

void igvEscena3D::setCuerpo(float cuerpo) {
    igvEscena3D::angCuerpo = cuerpo;
}

float igvEscena3D::getGiPierIzq() const {
    return giPierIzq;
}

void igvEscena3D::setGiPierIzq(float giPierIzq) {
    igvEscena3D::giPierIzq = giPierIzq;
}

float igvEscena3D::getGiPierDer() const {
    return giPierDer;
}

void igvEscena3D::setGiPierDer(float giPierDer) {
    igvEscena3D::giPierDer = giPierDer;
}

float igvEscena3D::getMovVaso() const {
    return movVaso;
}

void igvEscena3D::setMovVaso(float movVaso) {
    igvEscena3D::movVaso = movVaso;
}

void igvEscena3D::setAngVaso(float angVaso) {
    igvEscena3D::angVaso = angVaso;
}

void igvEscena3D::crearEscena() {
    //Vaso
    glPushMatrix();
    glTranslatef(0,-(angVaso/180),movVaso);
    glTranslated(0,1,2.5);
    glRotatef(angVaso,1,0,0);
    glRotatef(90, 1, 0, 0);
    glScalef(1,1,12);
    glutSolidTorus(0.1,0.6,50,50);
    glPopMatrix ();

    //Sombrero
    glPushMatrix();
    glRotatef(angCuerpo, 1, 0, 0);
    glTranslated(0,4,0);
    glScalef(1,1.5,1);
    glutSolidCube(0.6);
    glPopMatrix ();

    glPushMatrix();
    glRotatef(angCuerpo, 1, 0, 0);
    glTranslated(0,3.5,0);
    glScalef(1,0.1,1);
    glutSolidSphere(0.6,100,100);
    glPopMatrix ();

    //Pico
    glPushMatrix();
    glRotatef(angCuerpo, 1, 0, 0);
    glTranslated(0,3,0.5);
    glutSolidCone(0.1,0.5,100,100);
    glPopMatrix ();

    //Cabeza
    glPushMatrix();
    glRotatef(angCuerpo, 1, 0, 0);
    glTranslatef(0,3,0);
    glutSolidSphere(0.5,100,100);
    glPopMatrix();

    //Cuerpo
    glPushMatrix();
    glRotatef(angCuerpo, 1, 0, 0);
    glTranslatef(0,1.5,0);
    glScalef(0.5,2,0.5);
    glutSolidSphere(1,100,100);
    glPopMatrix();

    //Base de tr�angulos
    glPushMatrix();
    glTranslated(-0.5,0,0);
    glRotatef(giPierDer, 1,0,0);
    glRotatef(90,0,1,0);
    glRotatef(90,-1,0,0);
    glScalef(1,0.5,1);
    glColor3f(1,1,0);
    glutSolidCone(1,1,100,100);
    glPopMatrix ();

    glPushMatrix();
    glTranslated(0.5,0,0);
    glRotatef(giPierIzq, 1,0,0);
    glRotatef(90,0,1,0);
    glRotatef(90,-1,0,0);
    glScalef(1,0.5,1);
    glColor3f(1,1,0);
    glutSolidCone(1,1,100,100);
    glPopMatrix ();
}





