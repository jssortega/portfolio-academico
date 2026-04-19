//
// Created by admin on 20/09/2022.
//

#ifndef IMAGENES_CONTENEDORIMAGENES_H
#define IMAGENES_CONTENEDORIMAGENES_H
#include "Imagen.h"


class ContenedorImagenes {
private:
    unsigned int _tamMax;
    Imagen* _imagenes;
public:
    /**
     * Constructor por defecto
     * @brief Crea un contenedor con 100 posiciones disponibles */
    ContenedorImagenes();
    /**
     * Cosntructor parametrizado
     * @brief Crea un contenedor de tamMax posicines */
    explicit ContenedorImagenes(unsigned int tamMax);
    /** Constructor copia */
    ContenedorImagenes(const ContenedorImagenes &origen);
    /** Constructor de copia parcial */
    ContenedorImagenes (const ContenedorImagenes &origen, unsigned int posicionInicial, unsigned int numElementos);

    /** Operador de asignacion */
    ContenedorImagenes operator=(const ContenedorImagenes &origen);

    /**
     * @brief Añade una imagen
     * @param dato: la imagen que se asigna al contenedor
     * @param pos: la posicion en la que se asigna la imagen
     * */
    void asigna(const Imagen& dato,unsigned int pos);
    /** @brief Devuelve una imagen
     * @param pos: la posicion en la que se encuentra la imagen que se va a devolver
     * @return Imagen: devuelve una copia de la imagen que hay en esa posicion
     * */
    Imagen recupera(unsigned int pos);
    /** @brief Ordena el contenedor de menor a mayor */
    void ordenar();
    /** @brief Ordena el contenedor de mayor a menor */
    void ordenarRev();
    /** @return unsigned int: intDevuelve tamaño lógico */
    unsigned int tam();

    virtual ~ContenedorImagenes();
};


#endif //IMAGENES_CONTENEDORIMAGENES_H
