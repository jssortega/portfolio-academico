#include "igvFigura.h"

#include <cmath>
#include "iostream"
#include "cmath"


/**
 * Constructor por defecto
 */
igvFigura::igvFigura() : igvMallaTriangulos()
{
}

/**
 * Constructor parametrizado
 * @param r Radio de la base del cilindro
 * @param a Altura del cilindro
 * @param divU N�mero de divisiones laterales
 * @param divV N�mero de divisiones en altura
 * @param nada Diferencia que el constructor es para el cilindro
 * @pre Se asume que los par�metros tienen valores v�lidos
 * @post Se crea una nueva malla de tri�ngulos que representa la cara lateral de
 *       un cilindro con altura a y radio r
 */
igvFigura::igvFigura(float r, float a, int divU, int divV, int nada)
{
    float subida = a/divV;
    float subAngulo = 360/divU, angulo = 0;
    float y = 0, x  = 0, z =0;

    num_verticesCilindro = divU * divV + divU;
    verticesCilindro = new float[num_verticesCilindro * 3];
    num_triangulosCilindro = divU * divV * 2;
    triangulosCilindro = new unsigned int[num_triangulosCilindro * 3];
    float PI = 3.14159265359/180;
    num_triangulosCilindro = 0;
    num_verticesCilindro = 0;
    for(int i = 0; i < divV + 1; ++i){

        for (int j = 0; j < divU; ++j) {
            x = r * std::cos(angulo*PI);
            z = r * std::sin(angulo*PI);
            igvMallaTriangulos::verticesCilindro[num_verticesCilindro++] = x;
            igvMallaTriangulos::verticesCilindro[num_verticesCilindro++] = y;
            igvMallaTriangulos::verticesCilindro[num_verticesCilindro++] = z;

            angulo += subAngulo;
        }

        y += subida;
    }
    for (int i = 0; i < divU * divV; ++i) {
        if((i+1)%divU==1 && i!=0){
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i + 1 - divU;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i + divU;
        }else {
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i + 1;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i + divU;
        }
    }

    for (int i = (divU * divV)+divU-1; i > divU-1; --i) {
        if((i)%divU==1){
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i - 1 + divU;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i - divU;
        }else {
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i - 1;
            igvMallaTriangulos::triangulosCilindro[num_triangulosCilindro++] = i - divU;
        }
    }

 }

/**
* Constructor parametrizado
* @param l anchura de la cara del cuadrado
* @param a Altura de la cara del cuadrado
* @param divU N�mero de divisiones laterales
* @param divV N�mero de divisiones en altura
* @pre Se asume que los par�metros tienen valores v�lidos
* @post Se crea una nueva malla de tri�ngulos que representa
*       una cara con altura a y anchura l
*/
 igvFigura::igvFigura(double l, float a, int divU, int divV)
{
    float subida = a/divV;
    float desplazamiento = l/divU;
    float y = 0, x  = 0, z =0;

    num_verticesCuadrado = divU * divV + divU;
    verticesCuadrado = new float[num_verticesCuadrado * 3];
    num_triangulosCuadrado = divU * divV * 2;
    triangulosCuadrado = new unsigned int[num_triangulosCuadrado * 3];
    num_triangulosCuadrado = 0;
    num_verticesCuadrado = 0;
    for(int i = 0; i < divV + 1; ++i){

        for (int j = 0; j < divU; ++j) {
            igvMallaTriangulos::verticesCuadrado[num_verticesCuadrado++] = x;
            igvMallaTriangulos::verticesCuadrado[num_verticesCuadrado++] = y;
            igvMallaTriangulos::verticesCuadrado[num_verticesCuadrado++] = z;
            x+= desplazamiento;
        }
        x=0;
        y += subida;
    }
    for (int i = 0; i < divU * divV; ++i) {
        if((i+1)%divU==1 && i!=0){
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i + 1 - divU;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i + divU;
        }else {
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i + 1;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i + divU;
        }
    }

    for (int i = (divU * divV)+divU-1; i > divU-1; --i) {
        if((i)%divU==1){
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i - 1 + divU;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i - divU;
        }else {
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i - 1;
            igvMallaTriangulos::triangulosCuadrado[num_triangulosCuadrado++] = i - divU;
        }
    }
}
/**
 * Destructor
 */
igvFigura::~igvFigura()
{
}
