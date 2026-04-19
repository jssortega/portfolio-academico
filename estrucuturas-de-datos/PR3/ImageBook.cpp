//
// Created by gabis on 12/10/2022.
//

#include <sstream>
#include <fstream>
#include <iostream>
#include "ImageBook.h"
#include "fecha.h"
#include "Imagen.h"

ImageBook::ImageBook(std::string etiquetas, std::string usuarios, std::string imagenes): _images(10000) {
    leerEtiquetas(etiquetas);
    leerUsuarios(usuarios);
    leerImagenes(imagenes);
}

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

void ImageBook::leerUsuarios(std::string fich) {
    std::ifstream entrada(fich);
    std::string email;
    if(entrada.good()){
        while(getline(entrada,email)){
            Usuario user(email);
            _users.inserta(user);
        }
        entrada.close();
    }else{
        throw std::string ("ImageBook::leerUsuarios: Error apertura del fichero");
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
                //    if(etiquetaStr == it._dato().getNombre()){
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
                Imagen imagen(id, nombre, tam, fecha, etiquetaPtr);

                _images.insertar(imagen);
                Usuario usuario(email);
                _users.buscaIt(usuario)->insertarImagen(&_images[_images.tamlog()-1]);
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

VDinamico<Usuario *> ImageBook::buscarUsuarioEtiq(std::string etiqueta) {
    VDinamico<Usuario *> retorno;
    VDinamico<Usuario *> usuarios = _users.recorreInorden();
    for (int i = 0; i < usuarios.tamlog(); ++i) {
        VDinamico<Imagen *> images = usuarios[i]->Images();
        for (int j = 0; j < images.tamlog(); ++j) {
            if(images[j]->getEtiqueta() == etiqueta){
                retorno.insertar(usuarios[i]);
                break;
            }
        }
    }
    return retorno;
}

VDinamico<Usuario *> ImageBook::getMasActivos() {
    VDinamico<Usuario*> retorno;
    VDinamico<Usuario *> usuarios = _users.recorreInorden();
    for (int i = 0; i < usuarios.tamlog(); ++i) {
        if(retorno.tamlog() == 0 || retorno[0]->getNumImages() < usuarios[i]->getNumImages()){
            retorno.vaciar();
            retorno.insertar(usuarios[i]);
        }else if(retorno[0]->getNumImages() == usuarios[i]->getNumImages()){
            retorno.insertar(usuarios[i]);
        }
    }
    return retorno;
}




