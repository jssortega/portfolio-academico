#include "igvMaterial.h"

// M�todos constructores

/**
 * Constructor de copia
 * @param p Material del que se copian las propiedades
 */
igvMaterial::igvMaterial ( const igvMaterial &p ): Ka ( p.Ka ), Kd ( p.Kd )
                                                   , Ks ( p.Ks ), Ns ( p.Ns )
{}

/**
 * Constructor parametrizado
 * @param _Ka Valor para el coeficiente de reflexi�n ambiental
 * @param _Kd Valor para el coeficiente de reflexi�n difusa
 * @param _Ks Valor para el coeficiente de reflexi�n especular
 * @param _Ns Valor para el exponente de Phong
 */
igvMaterial::igvMaterial ( igvColor _Ka, igvColor _Kd, igvColor _Ks, double _Ns ):
                         Ka ( _Ka ), Kd ( _Kd ), Ks ( _Ks ), Ns ( _Ns )
{}

// M�todos p�blicos

/**
 * M�todo para aplicar las propiedades del material llamando a las funciones
 * de OpenGL
 */
void igvMaterial::aplicar ()
{

// TODO: APARTADO B
// Aplicar los valores de los atributos del objeto igvMaterial:
// - coeficiente de reflexi�n de la luz ambiental
// - coeficiente de reflexi�n difuso
// - coeficiente de reflexi�n especular
// - exponente de Phong


// Coeficientes y exponente proporcionados
    GLfloat coeficiente_ambiental[] = {0.15, 0, 0, 0.0};
    GLfloat coeficiente_difuso[] = {0.5, 0, 0, 0.0};
    GLfloat coeficiente_especular[] = {0.5, 0.0, 0.0, 0.0};
    GLint exponente_phong = 120;

    // Aplicar los coeficientes y el exponente de Phong
    glMaterialfv(GL_FRONT, GL_AMBIENT, coeficiente_ambiental);
    glMaterialfv(GL_FRONT, GL_DIFFUSE, coeficiente_difuso);
    glMaterialfv(GL_FRONT, GL_SPECULAR, coeficiente_especular);
    glMateriali(GL_FRONT, GL_SHININESS, exponente_phong);

    // Color de emisión (el objeto no es una fuente de luz)
    GLfloat color_emision[] = {0.0, 0.0, 0.0, 0.0};

    // Aplicar el color de emisión
    glMaterialfv(GL_FRONT, GL_EMISSION, color_emision);
}

/**
 * Cambia las propiedades del material
 * @param _Ka Valor para el coeficiente de reflexi�n ambiental
 * @param _Kd Valor para el coeficiente de reflexi�n difusa
 * @param _Ks Valor para el coeficiente de reflexi�n especular
 * @param _Ns Valor para el exponente de Phong
 * @pre Se asume que los par�metros tienen valores v�lidos
 * @post Las propiedades del material cambian
 */
void igvMaterial::set ( igvColor _Ka, igvColor _Kd, igvColor _Ks, double _Ns )
{  Ka = _Ka;
   Kd = _Kd;
   Ks = _Ks;
   Ns = _Ns;
}

const igvColor &igvMaterial::getKa() const {
    return Ka;
}

const igvColor &igvMaterial::getKd() const {
    return Kd;
}

const igvColor &igvMaterial::getKs() const {
    return Ks;
}

double igvMaterial::getNs() const {
    return Ns;
}



