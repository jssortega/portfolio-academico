//
// Created by gabis on 12/10/2022.
//

#include <sstream>
#include <fstream>
#include <iostream>
#include <algorithm>
#include "ImageBook.h"
#include "fecha.h"
#include "Imagen.h"

ImageBook::ImageBook(std::string etiquetas, std::string usuarios, std::string imagenes){
    _images.reserve(10000);
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
            _labels.push_back(label);
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
            _users[email] = Usuario(email,this);
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
    std::deque<Etiqueta*> etiquetas;
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

                etiquetas.clear();
                while (getline(columnas,etiquetaStr,',')){
                    etiqueta = Etiqueta(etiquetaStr);
                    list<Etiqueta>::iterator itEtiq = std::find(_labels.begin(), _labels.end(), etiqueta);
                    itEtiq != _labels.end() ? etiquetaPtr = &(*find(_labels.begin(), _labels.end(), etiqueta)) : etiquetaPtr = nullptr;
                    etiquetas.push_back(etiquetaPtr);
                }


                //ListaDEnlazada<Etiqueta>::Iterador it = _labels.iterador();
                //while (it.haySiguiente()){
                //    if(etiquetaStr == it._dato().getNombre()){
                //        etiqueta = &(*it);
                //        break;
                //    }
                //    it.siguiente();
                //}



                fila="";
                columnas.clear();

                fecha.asignarDia(dia,mes,anno);
                Imagen imagen(id, nombre, tam, fecha,etiquetas);

                _images.push_back(imagen);
                _users.at(email).insertarImagen(&_images[_images.size()-1]);
            }
        }
        entrada.close();
    } else {
        throw std::string ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
}

list<Imagen*> ImageBook::buscarImagEtiq(std::string etiqueta) {
    list<Imagen*> retorno;
    for (int i = 0; i < _images.size(); ++i) {
        for (auto & _etiqueta: _images[i].getEtiquetada()) {
            if(_etiqueta->getNombre() == etiqueta){
                retorno.push_back(&_images[i]);
            }
        }

    }
    return retorno;
}

Imagen *ImageBook::buscaImagen(std::string id) {
    for (int i = 0; i < _images.size(); ++i) {
        if(_images[i].getId() == id) return &_images[i];
    }
    return nullptr;
}

std::string ImageBook::etiquetaMasRepetida() {
    list<Etiqueta>::iterator itEtiq = _labels.begin();
    int mayor = 0;
    int cur = 0;
    std::string repetida;
    while (itEtiq != _labels.end()) {
        for (int i = 0; i < _images.size(); ++i) {
            //Uso comparación de direcciones para mayor velocidad
            for (auto & _etiqueta: _images[i].getEtiquetada()) {
                if (&(*itEtiq) == _etiqueta) {
                    ++cur;
                }
            }
        }
        if (cur > mayor) {
            mayor = cur;
            repetida = itEtiq->getNombre();
        }
        cur = 0;
        itEtiq++;
    }
    return repetida;
}

vector<Usuario *> ImageBook::buscarUsuarioEtiq(std::string etiqueta) {
    vector<Usuario *> retorno;
    bool premisa;
    for(auto & user : _users){
        premisa = false;
        for (auto & Image : user.second.getUserImages()) {
            for (auto & _etiqueta: Image.second->getEtiquetada()) {
                if(_etiqueta->getNombre() == etiqueta){
                    retorno.push_back(&user.second);
                    premisa = true;
                    break;
                }
            }
            if(premisa) break;
        }
    }

    return retorno;
}

vector<Usuario *> ImageBook::getMasActivos() {
    vector<Usuario*> retorno;
    for(auto & user : _users){
        if(retorno.size() == 0 || retorno[0]->getNumImages() < user.second.getNumImages()){
            retorno.clear();
            retorno.push_back(&user.second);
        }else if(retorno[0]->getNumImages() == user.second.getNumImages()){
            retorno.push_back(&user.second);
        }
    }
    return retorno;
}

Etiqueta *ImageBook::buscaEtiqueta(std::string nombreEti) {
    for (auto & label : _labels) {
        if(label.getNombre() == nombreEti) return &label;
    }
    return nullptr;
}

vector<Usuario *> ImageBook::buscarUsuarioFechaImagen(Fecha fecha) {
    vector<Usuario*> retorno;
    for(auto & user : _users){
        for(auto & image : user.second.getUserImages()){
            if(image.second->getFecha().cadenaDia() == fecha.cadenaDia()) {
                retorno.push_back(&user.second);
                break;
            }
        }
    }
    return retorno;
}

vector<Usuario *> ImageBook::buscarUsuariosPremium() {
    vector<Usuario*> retorno;
    for(auto & user : _users){
        if(retorno.size() == 0 || retorno[0]->getImagenMasAntigua()->getFecha() > user.second.getImagenMasAntigua()->getFecha()){
            retorno.clear();
            retorno.push_back(&user.second);
        }else if(!(retorno[0]->getImagenMasAntigua()->getFecha() < user.second.getImagenMasAntigua()->getFecha())){
            retorno.push_back(&user.second);
        }
    }
    return retorno;
}






