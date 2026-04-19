//
// Created by gabis on 12/10/2022.
//

#include <sstream>
#include <fstream>
#include <iostream>
#include "ImageBook.h"
#include "fecha.h"
#include "Imagen.h"

void ImageBook::leerEtiquetas(std::string fich) {
    std::ifstream entrada(fich);
    std::string nombre;
    if(entrada.good()){
        while(getline(entrada,nombre)){
            Etiqueta label(nombre);
            _labels.insertarFin(label);
        }
        entrada.close();
    }else{
        throw std::string ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
}

void ImageBook::leerImagenes(std::string fich) {
    std::ifstream entrada;
    std::stringstream  columnas;
    std::string fila;

    Fecha fecha;
    std::string id = "";
    std::string email="";
    std::string nombre;
    std::string etiquetaStr;
    Etiqueta etiqueta;
    Etiqueta* etiquetaPtr;
    int tam = 0;
    int dia = 0;
    int mes = 0;
    int anno = 0;

    entrada.open(fich);
    if ( entrada.good() ) {
        while ( getline(entrada, fila ) ) {
            if (fila!="") {

                columnas.str(fila);

                getline(columnas, id, ';');
                getline(columnas,email,';');
                getline(columnas,nombre,';');

                columnas >> tam;
                columnas.ignore();
                columnas >> dia; columnas.ignore();
                columnas >> mes; columnas.ignore();
                columnas >> anno; columnas.ignore();

                getline(columnas,etiquetaStr,',');

                //ListaDEnlazada<Etiqueta>::Iterador it = _labels.iterador();
                //while (it.haySiguiente()){
                //    if(etiquetaStr == it.dato().getNombre()){
                //        etiqueta = &(*it);
                //        break;
                //    }
                //    it.siguiente();
                //}
                etiqueta = Etiqueta(etiquetaStr);
                ListaDEnlazada<Etiqueta>::Iterador itEtiq = _labels.busca(etiqueta);

                itEtiq.haySiguiente() ? etiquetaPtr = &(*_labels.busca(etiqueta)) : etiquetaPtr = nullptr;


                fila="";
                columnas.clear();

                fecha.asignarDia(dia,mes,anno);
                Imagen imagen(id, email, nombre, tam, fecha, etiquetaPtr);

                _images.insertar(imagen);
            }
        }
        entrada.close();
    } else {
        throw std::string ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
}

ListaDEnlazada<Imagen*> ImageBook::buscarImagEtiq(std::string etiqueta) {
    ListaDEnlazada<Imagen*> retorno;
    Imagen*  imagen;
    for (int i = 0; i < _images.tamlog(); ++i) {
        if(_images[i].getEtiqueta() == etiqueta){
            imagen = &_images[i];
            retorno.insertarFin(imagen);
        }
    }

    return retorno;
}

std::string ImageBook::etiquetaMasRepetida() {
    ListaDEnlazada<Etiqueta>::Iterador itEtiq = _labels.iterador();
    int mayor = 0;
    int cur = 0;
    std::string repetida;
    while (itEtiq.haySiguiente()) {
        for (int i = 0; i < _images.tamlog(); ++i) {
            //Uso comparación de direcciones para mayor velocidad
            if (&itEtiq.dato() == _images[i].getEtiquetada()) {
                ++cur;
            }
        }
        if (cur > mayor) {
            mayor = cur;
            repetida = itEtiq.dato().getNombre();
        }
        cur = 0;
        itEtiq.siguiente();
    }
    return repetida;
}
