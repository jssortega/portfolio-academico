//
// Created by admin on 20/09/2022.
//

#include "Imagen.h"


Imagen::Imagen(const string &_id, const string &_email, const string &_nombre, unsigned int _tam, const Fecha &_fecha,
               const string &_etiquetas) : _id(_id), _email(_email), _nombre(_nombre), _tam(_tam), _fecha(_fecha),
                                          _etiquetas(_etiquetas) {}

Imagen::Imagen():_id(""), _email(""), _nombre(""), _tam(0),_etiquetas("") {
}

Imagen Imagen::operator=(const Imagen &asignacion) {
    if (this != &asignacion){
        _id = asignacion._id;
        _email = asignacion._email;
        _etiquetas = asignacion._etiquetas;
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

const string &Imagen::getId() const {
    return _id;
}

const string &Imagen::getEmail() const {
    return _email;
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

const string &Imagen::getEtiquetas() const {
    return _etiquetas;
}

Imagen::~Imagen() {}

ostream &operator<<(ostream &os, const Imagen &imagen) {
    os << "Imagen: ( ID=" << imagen.getId()
       << " Email=" << imagen.getEmail() << " Fichero=" << imagen.getNombre() << " Tam=" << imagen.getTam()
       << " Fecha=" << imagen.getFecha().cadenaDia()
       << " Etiquetas=" << imagen.getEtiquetas()
       << ")" << std::endl;
    return os;
}

