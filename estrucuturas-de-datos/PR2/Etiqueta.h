//
// Created by gabis on 12/10/2022.
//

#ifndef IMAGENES_ETIQUETA_H
#define IMAGENES_ETIQUETA_H

#include <string>

class Etiqueta{
    std::string _nombre;
public:
    /** Constructor por defecto */
    Etiqueta(): _nombre(""){}
    /** Constructor copia */
    Etiqueta(std::string nombre): _nombre(nombre){};

    /** Operadores de equidad */
    bool operator==(const Etiqueta &rhs) const {
        return _nombre == rhs._nombre;
    }
    bool operator!=(const Etiqueta &rhs) const {
        return !(rhs == *this);
    }
    /** Getter */
    std::string getNombre(){return _nombre;};
};

#endif //IMAGENES_ETIQUETA_H
