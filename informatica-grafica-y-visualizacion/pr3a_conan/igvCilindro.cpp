#include "igvCilindro.h"

#include <cmath>
#include "iostream"
#include "cmath"


/**
 * Constructor por defecto
 */
igvCilindro::igvCilindro() :igvMallaTriangulos()
{
}

/**
 * Constructor parametrizado
 * @param r Radio de la base del cilindro
 * @param a Altura del cilindro
 * @param divU Número de divisiones laterales
 * @param divV Número de divisiones en altura
 * @pre Se asume que los parámetros tienen valores válidos
 * @post Se crea una nueva malla de triángulos que representa la cara lateral de
 *       un cilindro con altura a y radio r
 */

//x=r*cos(angulo)*(area porcion)

igvCilindro::igvCilindro(float r, float a, int divU, int divV)
{	// TODO: Apartado B: Construir la malla de triángulos para representar el cilindro
	// TODO: Apartado C: Añadir el vector de normales
    float subida = a/divV;
    float subAngulo = 360/divU, angulo = 0;
    float y = 0, x  = 0, z =0;

    num_vertices = divU*divV+divU;
    vertices = new float[num_vertices * 3];
    num_triangulos = divU*divV*2;
    triangulos = new unsigned int[num_triangulos * 3];
    float PI = 3.14159265359/180;
    num_triangulos = 0;
    num_vertices = 0;
    for(int i = 0; i < divV + 1; ++i){

        for (int j = 0; j < divU; ++j) {
            x = r * std::cos(angulo*PI);
            z = r * std::sin(angulo*PI);
            igvMallaTriangulos::vertices[num_vertices++] = x;
            igvMallaTriangulos::vertices[num_vertices++] = y;
            igvMallaTriangulos::vertices[num_vertices++] = z;

            angulo += subAngulo;
        }

        y += subida;
    }
    for (int i = 0; i < divU * divV; ++i) {
        if((i+1)%divU==1 && i!=0){
            igvMallaTriangulos::triangulos[num_triangulos++] = i;
            igvMallaTriangulos::triangulos[num_triangulos++] = i+1-divU;
            igvMallaTriangulos::triangulos[num_triangulos++] = i+divU;
        }else {
            igvMallaTriangulos::triangulos[num_triangulos++] = i;
            igvMallaTriangulos::triangulos[num_triangulos++] = i+1;
            igvMallaTriangulos::triangulos[num_triangulos++] = i+divU;
        }
    }

    for (int i = (divU * divV)+divU-1; i > divU-1; --i) {
        if((i)%divU==1){
            igvMallaTriangulos::triangulos[num_triangulos++] = i;
            igvMallaTriangulos::triangulos[num_triangulos++] = i-1+divU;
            igvMallaTriangulos::triangulos[num_triangulos++] = i-divU;
        }else {
            igvMallaTriangulos::triangulos[num_triangulos++] = i;
            igvMallaTriangulos::triangulos[num_triangulos++] = i-1;
            igvMallaTriangulos::triangulos[num_triangulos++] = i-divU;
        }
    }
 }

/**
 * Destructor
 */
igvCilindro::~igvCilindro()
{
}
