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

ImageBook::ImageBook(std::string etiquetas, std::string usuarios, std::string imagenes): _images(10000,0.68){
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
                Imagen* imagen = new Imagen(id, nombre, tam, fecha,id[id.length()-1]-48+(id[id.length()-2]-48)*10+(id[id.length()-3]-48)*100,etiquetas);

                _images.insertar(djb2(id),imagen);
                for(auto etiqueta : etiquetas){
                    etiqueta->nuevaImagen(_images.buscar(djb2(id)));
                }
                _users.at(email).insertarImagen(_images.buscar(djb2(id)));
            }
        }
        entrada.close();
    } else {
        throw std::string ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
}

std::vector<Imagen*> ImageBook::buscarImagEtiq(std::string etiqueta) {
    auto etiq = std::find(_labels.begin(),_labels.end(),Etiqueta(etiqueta));
    return etiq != _labels.end() ? vector<Imagen*>():etiq->getImages();
}

Imagen *ImageBook::buscaImagen(std::string id) {
    return _images.buscar(djb2(id));
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

unsigned long ImageBook::djb2(std::string cadena) {
    const char* str = cadena.c_str();
    unsigned long hash = 97499;
    int c;
    while ((c = *str++)) hash = ((hash << 5) + hash) + c;
    return hash;
}

vector<Etiqueta *> ImageBook::getMasLikes() {
    vector<Etiqueta*> retorno;
    for(auto & etiqueta : _labels){
        if(retorno.size() == 0 || retorno[0]->getTotalLikes() < etiqueta.getTotalLikes()){
            retorno.clear();
            retorno.push_back(&etiqueta);
        }else if(retorno[0]->getTotalLikes() == etiqueta.getTotalLikes()){
            retorno.push_back(&etiqueta);
        }
    }
    return retorno;
}

void ImageBook::nuevaImagen(Imagen &img,std::string email) {
    _images.insertar(djb2(img.getId()),&img);
    for(auto etiqueta : img.getEtiquetada()){
        etiqueta->nuevaImagen(_images.buscar(djb2(img.getId())));
    }
    _users.at(email).insertarImagen(_images.buscar(djb2(img.getId())));
}

std::vector<Etiqueta*> ImageBook::top5Etiq() {
    std::vector<Etiqueta*> retorno(5);
    vector<int> likes(6,0);
    for(auto & etiqueta : _labels){
        likes[0] = etiqueta.getTotalLikes();
        for (int i = 0; i < 5; ++i) {
            if(likes[0]>likes[i+1]){
                retorno[i] = &etiqueta;
                likes[i+1] = likes[0];
                break;
            }
        }
    }
    return retorno;
}

std::vector<Usuario *> ImageBook::top3User() {
    Usuario u = Usuario();
    std::vector<Usuario*> retorno(3,&u);
    int popularidad;
    for(auto & user : _users){
        popularidad = user.second.actualizarPopularidad();
        for (int i = 0; i < 3; ++i) {
            if(popularidad>retorno[i]->getPopularidad()){
                retorno[i] = &user.second;
                break;
            }
        }
    }
    return retorno;
}

void ImageBook::borrarImg(std::string id) {
    Imagen* borrar = _images.buscar(djb2(id));
    for(auto & user : buscarUsuarioEtiq(borrar->getEtiquetada()[0]->getNombre())){
        if(user->getUserImages().find(id) != user->getUserImages().end()){
            user->eliminarImagen(id);
        }
    }
    for(auto & etiqueta : borrar->getEtiquetada()){
        etiqueta->eliminarImagen(borrar);
    }
    _images.borrar(djb2(id));
}






