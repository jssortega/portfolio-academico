//
// Created by gabis on 26/10/2022.
//

#include "Usuario.h"
#include "ImageBook.h"
#include <utility>

Usuario::Usuario() : _email(""),_popularidad(0){}

Usuario::Usuario(std::string email, ImageBook* link) : _email(std::move(email)),_linkIB(link){}

bool Usuario::operator<(const Usuario &rhs) const {
    return _email < rhs._email;
}

bool Usuario::operator>(const Usuario &rhs) const {
    return rhs < *this;
}

bool Usuario::operator<=(const Usuario &rhs) const {
    return !(rhs < *this);
}

bool Usuario::operator>=(const Usuario &rhs) const {
    return !(*this < rhs);
}

bool Usuario::operator==(const Usuario &rhs) const {
    return _email == rhs._email;
}

bool Usuario::operator!=(const Usuario &rhs) const {
    return !(rhs == *this);
}

vector<Imagen *> Usuario::buscarEtiq(std::string nombreEtiq) {
    vector<Imagen*> retorno;
    for (auto & image: _userImages) {
        for (auto & _etiqueta: image.second->getEtiquetada()) {
            if(_etiqueta->getNombre() == nombreEtiq){
                retorno.push_back(image.second);
            }
        }

    }
    return retorno;
}

bool Usuario::esMasActivo() {
    vector<Usuario*> usuarios = _linkIB->getMasActivos();
    return std::find(usuarios.begin(),usuarios.end(),this) != usuarios.end();
}

vector<Usuario *> Usuario::buscarUsuariosEtiq(string nombreEti) {
    return _linkIB->buscarUsuarioEtiq(nombreEti);
}

void Usuario::anadirEtiquetaImagen(std::string id, std::string nombreEtiq) {
    _userImages.find(id)->second->anadirEtiqueta(&*std::find(_linkIB->_labels.begin(),_linkIB->_labels.end(),Etiqueta(nombreEtiq)));
}

std::vector<Imagen *> Usuario::getImagenesEtiqueta(string nombreEti) {
    return _linkIB->buscarImagEtiq(nombreEti);
}

void Usuario::meGustaImagen(Imagen * imagen) {
    Imagen* encontrado = _linkIB->buscaImagen(imagen->getId());
    if(encontrado) encontrado->nuevoLike();
}

void Usuario::likeAutomatico(std::string nombreEtiq) {
    auto imagenes = buscarEtiq(nombreEtiq);
    for(auto & imagen : imagenes){
        imagen->nuevoLike();
    }
}

const int& Usuario::actualizarPopularidad() {
    _popularidad = 0;
    for(auto & image : _userImages){
        _popularidad += image.second->getLikes();
    }
    return _popularidad;
}

void Usuario::recorrerUserImages(const std::function<bool(pair<const string,Imagen*>&)>& func) {
    for(auto & image : _userImages){
        if(func(image))break;
    }
}

std::vector<Imagen *> Usuario::imagenEnZona(float rxmin, float rymin, float rxmax, float rymax) {
    std::vector<Imagen *> retorno;
    for(auto & imagen : _linkIB->_imagesPos.buscarRango(rxmin,rymin,rxmax,rymax)){
        if(contieneImagen(imagen->getId())) retorno.push_back(imagen);
    }
    return retorno;
}

void Usuario::likeAutomaticoZona(float rxmin, float rymin, float rxmax, float rymax) {
    for(auto & imagen : _linkIB->_imagesPos.buscarRango(rxmin,rymin,rxmax,rymax)){
        meGustaImagen(imagen);
    }
}
