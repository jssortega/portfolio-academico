//
// Created by admin on 20/09/2022.
//

#include "Imagen.h"

#include <utility>


Imagen::Imagen(string _id, string _nombre, unsigned int _tam, const Fecha &_fecha,std::deque<Etiqueta*> etiquetada)
               : _id(std::move(_id)), _nombre(std::move(_nombre)), _tam(_tam), _fecha(_fecha),_etiquetada(std::move(etiquetada)) {}

Imagen::Imagen(): _tam(0),_etiquetada() {_fecha.asignarDia(0,0,0);}

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
    os << "(" << imagen.getId() << ", " << imagen._nombre << ", " << imagen._fecha.verDia() << ")" << std::endl;
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

Fecha &Imagen::getFecha() {
    return _fecha;
}

const deque<Etiqueta *> &Imagen::getEtiquetada() const {
    return _etiquetada;
}

Imagen::~Imagen() = default;





