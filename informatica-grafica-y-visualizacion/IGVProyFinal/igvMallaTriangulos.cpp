#include <cstdlib>
#include <stdio.h>
#include <math.h>
#include "igvMallaTriangulos.h"
#include "iostream"

/**
 * Constructor parametrizado de una malla de tri�ngulos sin normales en los
 * v�rtices
 * @param _num_vertices N�mero de v�rtices de la nueva malla
 * @param _vertices Direcci�n de memoria donde se encuentran almacenadas las
 *        coordenadas (formato X,Y,Z) de los v�rtices. Esta informaci�n se
 *        copia en la nueva malla
 * @param _num_triangulos N�mero de tri�ngulos que forman la malla
 * @param _triangulos �ndices (formato v1, v2, v3) a los v�rtices que forman
 *        cada tri�ngulo. Esta informaci�n se copia en el nuevo objeto
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 * @post La nueva malla almacenar� copias de la informaci�n que se le pasa como
 *       par�metro
 */
igvMallaTriangulos::igvMallaTriangulos ( long int _num_vertices, float *_vertices
                                         , long int _num_triangulos
                                         , unsigned int *_triangulos ):
        num_verticesCuadrado (_num_vertices )
                                       , num_triangulosCuadrado (_num_triangulos ),
                                       num_verticesCilindro (_num_vertices),
                                       num_triangulosCilindro (_num_triangulos)
{
    verticesCilindro = new float[num_verticesCilindro * 3];
   for ( long int i = 0 ; i < ( num_verticesCilindro * 3 ) ; ++i )
   {  verticesCilindro[i] = _vertices[i];
   }

   triangulosCilindro = new unsigned int[num_triangulosCilindro * 3];
   for ( long int i = 0 ; i < ( num_triangulosCilindro * 3 ) ; ++i )
   {  triangulosCilindro[i] = _triangulos[i];
   }
    verticesCuadrado = new float[num_verticesCuadrado * 3];
    for (long int i = 0 ; i < (num_verticesCuadrado * 3 ) ; ++i )
    {  verticesCuadrado[i] = _vertices[i];
    }

    triangulosCuadrado = new unsigned int[num_triangulosCuadrado * 3];
    for (long int i = 0 ; i < (num_triangulosCuadrado * 3 ) ; ++i )
    {  triangulosCuadrado[i] = _triangulos[i];
    }
}

/**
 * Destructor
 */
igvMallaTriangulos::~igvMallaTriangulos ()
{  if ( verticesCilindro )
   {  delete []verticesCilindro;
      verticesCilindro = nullptr;
   }

   if ( triangulosCilindro )
   {  delete []triangulosCuadrado;
      triangulosCuadrado = nullptr;
   }

    if ( verticesCuadrado )
    {  delete []verticesCilindro;
        verticesCilindro = nullptr;
    }

    if ( triangulosCuadrado )
    {  delete []triangulosCuadrado;
        triangulosCuadrado = nullptr;
    }
}

/**
 * M�todo con las llamadas OpenGL para visualizar la malla de tri�ngulos
 */
void igvMallaTriangulos::visualizar ( igvMallaTriangulos *malla, igvMallaTriangulos *malla2)
{
    float color[3] = { 1, 1, 0};   ///< Color RGB de la caja (Amarillo)
    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color ); ///< Aplica el color

    //PIERNAS
    glPushMatrix();

    glTranslatef(0.67,-0.2,0);
    glRotatef(angPiernaDer,1,0,0);
    glTranslatef(-0.67,0.2,0);

    glTranslatef(0.67,-0.2,0);
    glRotatef(180,1,0,0);
    glScalef(1,0.7,1);
    for (int i = 0; i < num_triangulosCilindro*3; i+=3) {
        glBegin(GL_TRIANGLES);

        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+2]);

        glEnd();
    }
    glPopMatrix();

    glPushMatrix();

    glTranslatef(0.3,-0.2,0);
    glRotatef(angPiernaIzq,1,0,0);
    glTranslatef(-0.3,0.2,0.);

    glTranslatef(0.3,-0.2,0);
    glRotatef(180,1,0,0);
    glScalef(1,0.7,1);
    for (int i = 0; i < num_triangulosCilindro*3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA TRASERA
    glPushMatrix();
    glTranslatef(0,0,-0.25);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA DELANTERA
    glPushMatrix();
    glTranslatef(0,0,0.25);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA IZQUIERDA
    glPushMatrix();
    glTranslatef(0,0,-0.25);
    glRotatef(-90,0,1,0);
    glScalef(0.5,1,1);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA DERECHA
    glPushMatrix();
    glTranslatef(0.97,0,-0.25);
    glRotatef(-90,0,1,0);
    glScalef(0.5,1,1);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA ARRIBA
    glPushMatrix();
    glTranslatef(0,1,-0.25);
    glRotatef(90,1,0,0);
    glScalef(1,0.5,1);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //CARA ABAJO
    glPushMatrix();
    glTranslatef(0,0,-0.25);
    glRotatef(90,1,0,0);
    glScalef(1,0.5,1);
    for (int i = 0; i < num_triangulosCuadrado * 3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+1],malla->verticesCuadrado[malla->triangulosCuadrado[i+1]*3+2]);
        glVertex3f(malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3],malla->verticesCuadrado[malla->triangulosCuadrado[i+2]*3+1],malla->verticesCuadrado[triangulosCuadrado[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //BRAZO DERECHO
    glPushMatrix();
    glTranslatef(0.97,0.4,0);
    glRotatef(angBrazoDer,0,0,1);
    glTranslatef(-0.97,-0.4,0);

    glTranslatef(0.97,0.4,0);
    glRotatef(-90,0,0,1);
    for (int i = 0; i < num_triangulosCilindro*3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //Color de los brazos
    color[0] = 0.9;
    color[1] = 1;
    color[2] = 0;
    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );

    //BRAZO IZQUIERDO
    glPushMatrix();

    glTranslatef(0,0.4,0);
    glRotatef(angBrazoIzq,0,0,1);
    glTranslatef(0,-0.4,0);

    glTranslatef(0,0.4,0);
    glRotatef(90,0,0,1);
    for (int i = 0; i < num_triangulosCilindro*3; i+=3) {
        glBegin(GL_TRIANGLES);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+1]*3+2]);
        glVertex3f(malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+1],malla2->verticesCilindro[malla2->triangulosCilindro[i+2]*3+2]);
        glEnd();
    }
    glPopMatrix();

    //Color boca (Rojo)
    color[0] = 1;
    color[1] = 0;
    color[2] = 0;
    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );
    //BOCA
    glPushMatrix();
    glTranslatef(0.45,0.25,0.25);
    glScalef(0.75,0.25,0.25);
    glutSolidCube(0.5);

    glPopMatrix();

    //Color pantalon (Marron)
    color[0] = 0.6;
    color[1] = 0.4;
    color[2] = 0.2;

    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );

    //PANTALON
    glPushMatrix();
    glTranslatef(0.485,-0.1,0);
    glScalef(0.975,0.25,0.5);
    glutSolidCube(1);
    glPopMatrix();

    //ZAPATOS
    glPushMatrix();
    glRotatef(angZapaDer,1,0,0);
    glTranslatef(0.67,-0.7,0.05);
    glScalef(1,1,2);
    glutSolidCube(0.15);

    glPopMatrix();

    glPushMatrix();
    glRotatef(angZapaIzq,1,0,0);
    glTranslatef(0.3,-0.7,0.05);
    glScalef(1,1,2);
    glutSolidCube(0.15);

    glPopMatrix();

    //Color ojos (blanco)
    color[0] = 1;
    color[1] = 1;
    color[2] = 1;
    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );

    //OJOS
    glPushMatrix();
    glTranslatef(0.6,0.6,0.25);
    glutSolidSphere(0.1,100,100);

    glPopMatrix();

    glPushMatrix();
    glTranslatef(0.3,0.6,0.25);
    glutSolidSphere(0.1,100,100);

    glPopMatrix();

    //sombrero
    glPushMatrix();
    glTranslatef(gorroX,gorroY,0);
    glScalef(0.75,2,0.75);
    glutSolidSphere(0.1,100,100);
    glPopMatrix();

    //crustaceo crujiente: Aplicar textura al cubo
    igvTextura textura("/home/jortega/CLionProjects/IGVProyFinal/kk.png");
    textura.aplicar();
    glEnable(GL_TEXTURE_2D);

    glPushMatrix();

    glTranslatef(-3, 0, -1.2);
    glRotatef(180,1,0,0);
    glRotatef(90,0,1,0);

    glScalef(1, 1, 2);

    // Definir las coordenadas de textura para cada vértice del cubo
    float texCoords[8][2] = {
            {0.0, 0.0}, // Vértice 0 (inferior izquierdo)
            {1.0, 0.0}, // Vértice 1 (inferior derecho)
            {1.0, 1.0}, // Vértice 2 (superior derecho)
            {0.0, 1.0}, // Vértice 3 (superior izquierdo)
            {0.0, 0.0}, // Vértice 4 (inferior izquierdo)
            {1.0, 0.0}, // Vértice 5 (inferior derecho)
            {1.0, 1.0}, // Vértice 6 (superior derecho)
            {0.0, 1.0}  // Vértice 7 (superior izquierdo)
    };

    glBegin(GL_QUADS);

    // Cara frontal
    glTexCoord2fv(texCoords[0]);
    glVertex3f(-0.5, -0.5, 0.5);
    glTexCoord2fv(texCoords[1]);
    glVertex3f(0.5, -0.5, 0.5);
    glTexCoord2fv(texCoords[2]);
    glVertex3f(0.5, 0.5, 0.5);
    glTexCoord2fv(texCoords[3]);
    glVertex3f(-0.5, 0.5, 0.5);
    glEnd();

    glPopMatrix();


    glPushMatrix();
    glTranslatef(gorroX,gorroY,0);
    glTranslatef(0,-0.2,0.15);
    glScalef(0.75,0.2,2.5);
    glutSolidSphere(0.1,100,100);
    glPopMatrix();

    //Color iris (negro)
    color[0] = 0;
    color[1] = 0;
    color[2] = 0;
    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );

    //IRIS
    glPushMatrix();
    glTranslatef(0.6,0.6,0.34);
    glutSolidSphere(0.03,100,100);
    glPopMatrix();

    glPushMatrix();
    glTranslatef(0.3,0.6,0.34);
    glutSolidSphere(0.03,100,100);
    glPopMatrix();

    //TEXTURA PANTALON
    color[0] = 1;
    color[1] = 1;
    color[2] = 1;

    glMaterialfv ( GL_FRONT, GL_EMISSION, color );
    glColor3fv ( color );//Importante, es necesario para que lo reconozca el buffer de color a la hora de la selecci�n.
    igvTextura textura1("/home/jortega/CLionProjects/IGVProyFinal/pantalon.png");
    textura1.aplicar();
    glEnable(GL_TEXTURE_2D);

    glPushMatrix();
    glTranslatef(0.485, -0.1, 0.5005);
    glRotatef(180,0,0,1);
    glScalef(0.975, 0.25, 0.5);

    // Ajuste manual de las coordenadas de textura
    glBegin(GL_QUADS);
    glTexCoord2f(0.0, 0.0); glVertex3f(-0.5, -0.5, -0.5);
    glTexCoord2f(1.0, 0.0); glVertex3f( 0.5, -0.5, -0.5);
    glTexCoord2f(1.0, 1.0); glVertex3f( 0.5,  0.5, -0.5);
    glTexCoord2f(0.0, 1.0); glVertex3f(-0.5,  0.5, -0.5);
    glEnd();

    glPopMatrix();

}

long igvMallaTriangulos::getNumVerticesCuadrado() const {
    return num_verticesCuadrado;
}

long igvMallaTriangulos::getNumVerticesCilindro() const {
    return num_verticesCilindro;
}

float *igvMallaTriangulos::getVerticesCilindro() const {
    return verticesCilindro;
}

float *igvMallaTriangulos::getVerticesCuadrado() const {
    return verticesCuadrado;
}

long igvMallaTriangulos::getNumTriangulosCuadrado() const {
    return num_triangulosCuadrado;
}
long igvMallaTriangulos::getNumTriangulosCilindro() const {
    return num_triangulosCilindro;
}

unsigned int *igvMallaTriangulos::getTriangulosCilindro() const {
    return triangulosCilindro;
}
unsigned int *igvMallaTriangulos::getTriangulosCuadrado() const {
    return triangulosCuadrado;
}

float igvMallaTriangulos::getAngBrazoIzq() const {
    return angBrazoIzq;
}

void igvMallaTriangulos::setAngBrazoIzq(float angBrazoIzq) {
    igvMallaTriangulos::angBrazoIzq = angBrazoIzq;
}


void igvMallaTriangulos::setAngBrazoDer(float angBrazoDer) {
    igvMallaTriangulos::angBrazoDer = angBrazoDer;
}

int igvMallaTriangulos::getAngBrazoDer() const {
    return angBrazoDer;
}

int igvMallaTriangulos::getAngPiernaIzq() const {
    return angPiernaIzq;
}

int igvMallaTriangulos::getAngPiernaDer() const {
    return angPiernaDer;
}

void igvMallaTriangulos::setAngPiernaIzq(int angPiernaIzq) {
    igvMallaTriangulos::angPiernaIzq = angPiernaIzq;
}

void igvMallaTriangulos::setAngPiernaDer(int angPiernaDer) {
    igvMallaTriangulos::angPiernaDer = angPiernaDer;
}

float igvMallaTriangulos::getAngZapaIzq() const {
    return angZapaIzq;
}

void igvMallaTriangulos::setAngZapaIzq(int angZapaIzq) {
    igvMallaTriangulos::angZapaIzq = angZapaIzq;
}

float igvMallaTriangulos::getAngZapaDer() const {
    return angZapaDer;
}

void igvMallaTriangulos::setAngZapaDer(int angZapaDer) {
    igvMallaTriangulos::angZapaDer = angZapaDer;
}

float igvMallaTriangulos::getGorroY() const {
    return gorroY;
}

void igvMallaTriangulos::setGorroY(float gorroY) {
    igvMallaTriangulos::gorroY = gorroY;
}

float igvMallaTriangulos::getGorroX() const {
    return gorroX;
}

void igvMallaTriangulos::setGorroX(float gorroX) {
    igvMallaTriangulos::gorroX = gorroX;
}
