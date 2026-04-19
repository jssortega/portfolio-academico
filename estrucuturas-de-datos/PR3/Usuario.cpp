//
// Created by gabis on 26/10/2022.
//

#include "Usuario.h"

#include <utility>

Usuario::Usuario() : _email("") {}

Usuario::Usuario(std::string email) : _email(std::move(email)) {}

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

VDinamico<Imagen *> Usuario::buscarEtiq(std::string etiq) {
    VDinamico<Imagen*> retorno;
    for (int i = 0; i < userImages.tamlog(); ++i) {
        if (userImages[i]->getEtiqueta() == etiq){
            retorno.insertar(userImages[i]);
        }
    }
    return retorno;
}






