//
// Created by admin on 20/09/2022.
//

#ifndef IMAGENES_IMAGEN_H
#define IMAGENES_IMAGEN_H
#include <string>
#include <ostream>
#include "fecha.h"


class Imagen {
private:
    std::string _id;
    std::string _email;
    std::string _nombre;
    unsigned int _tam;
    Fecha _fecha;
    std::string _etiquetas;
public:
    /** Cosntructor por defecto */
    Imagen();
    /** Cronstructor parametrizado */
    Imagen(const string &_id, const string &_email, const string &_nombre, unsigned int _tam, const Fecha &_fecha,
           const string &_etiquetas);

    /** Operador de asignacion*/
    Imagen operator=(const Imagen &asignacion);
    /** Operadores de comparacion */
    bool operator<(const Imagen &rhs) const;
    bool operator>(const Imagen &rhs) const;

    friend ostream &operator<<(ostream &os, const Imagen &imagen);

    /** Getters */
    const string &getId() const;
    const string &getEmail() const;
    const string &getNombre() const;
    unsigned int getTam() const;
    const Fecha &getFecha() const;
    const string &getEtiquetas() const;

    /** Destructor */
    virtual ~Imagen();
};


#endif //IMAGENES_IMAGEN_H
