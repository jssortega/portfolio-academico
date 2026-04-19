//
// Created by admin on 20/09/2022.
//

#include "Imagen.h"

#include <utility>


Imagen::Imagen(string _id, string _nombre, unsigned int _tam, const Fecha &_fecha, Etiqueta *_etiqueta)
               : _id(std::move(_id)), _nombre(std::move(_nombre)), _tam(_tam), _fecha(_fecha),_etiquetada(_etiqueta) {}

Imagen::Imagen():_id(""), _nombre(""), _tam(0),_etiquetada(nullptr) {}

Imagen Imagen::operator=(const Imagen &asignacion) {
    if (this != &asignacion){
        _id = asignacion._id;
        _etiquetada = asignacion._etiquetada;
        _fecha = asignacion._fecha;
        _nombre = asignacion._nombre;
        _tam = asignacion._tam;
    }
    return *this;
}

bool Imagen::operator<(const Imagen &rhs) const {
    return _id < rhs._id;
}

bool Imagen::operator>(const Imagen &rhs) const {
    return rhs < *this;
}

bool Imagen::operator==(const Imagen &rhs) const {
    return _id == rhs._id;
}

bool Imagen::operator!=(const Imagen &rhs) const {
    return !(rhs == *this);
}

ostream &operator<<(ostream &os, const Imagen &imagen) {
    os << "(" << imagen.getId() << ", " << imagen._nombre << ")" << std::endl;
    return os;
}

const string &Imagen::getId() const {
    return _id;
}

const string &Imagen::getNombre() const {
    return _nombre;
}

unsigned int Imagen::getTam() const {
    return _tam;
}

const Fecha &Imagen::getFecha() const {
    return _fecha;
}

std::string Imagen::getEtiqueta(){
    return _etiquetada->getNombre();
}

Etiqueta *Imagen::getEtiquetada() const {
    return _etiquetada;
}

Imagen::~Imagen() {}





