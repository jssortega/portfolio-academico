//
// Created by gabis on 12/10/2022.
//

#ifndef IMAGENES_IMAGEBOOK_H
#define IMAGENES_IMAGEBOOK_H
#include "VDinamico.h"
#include "ListaDEnlazada.h"
#include "Etiqueta.h"
#include "Imagen.h"

class ImageBook {
private:
    VDinamico<Imagen> _images;
    ListaDEnlazada<Etiqueta> _labels;
public:
    /**@brief Rellena _labels con las etiquetas dadas en el fichero
     * @param fich: fichero con etiquetas*/
    void leerEtiquetas(std::string fich);
    /**@brief Rellena _images con los datos de las imagenes dadas en el fichero
     * @param fich: fichero con datos de imagenes*/
    void leerImagenes(std::string fich);
    /**@brief Busca la etiqueta más repetida en el vector _images
     * @return Un string con el nombre de la etiqueta más repetida*/
    std::string etiquetaMasRepetida();
    /**@brief Crea una lista doblemente enlazada de imagenes que contengan el nombre de la etiqueta
     * pasada por parametro
     * @param etiqueta: nombre de la etiqueta que se busca en la imagen
     * @return lista de imagenes con la etiqueta de nombre @param etiqueta*/
    ListaDEnlazada<Imagen*> buscarImagEtiq (string etiqueta);
};


#endif //IMAGENES_IMAGEBOOK_H
