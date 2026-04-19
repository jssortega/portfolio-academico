//
// Created by gabis on 26/10/2022.
//

#include "Usuario.h"
#include "ImageBook.h"
#include <utility>

Usuario::Usuario() : _email("") {}

Usuario::Usuario(std::string email, ImageBook* link) : _email(std::move(email)),_linkIB(link) {}

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

vector<Imagen *> Usuario::buscarEtiq(std::string nombreEtiq, Usuario& user) {
    vector<Imagen*> retorno;
    for (auto & image: user._userImages) {
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










