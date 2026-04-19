//
// Created by admin on 20/09/2022.
//

#ifndef IMAGENES_IMAGEN_H
#define IMAGENES_IMAGEN_H
#include <string>
#include <ostream>
#include "fecha.h"
#include "Etiqueta.h"


class Imagen {
private:
    std::string _id;
    std::string _nombre;
    unsigned int _tam;
    Fecha _fecha;
    Etiqueta *_etiquetada;
public:
    /** Cosntructor por defecto */
    Imagen();

    /** Constructor parametrizado */
    Imagen(string _id, string _nombre, unsigned int _tam, const Fecha &_fecha,
           Etiqueta* _etiquetada);

    /** Operador de asignacion*/
    Imagen operator=(const Imagen &asignacion);

    /** Operadores de comparacion */
    bool operator<(const Imagen &rhs) const;
    bool operator>(const Imagen &rhs) const;

    /** Operadores de equidad */
    bool operator==(const Imagen &rhs) const;
    bool operator!=(const Imagen &rhs) const;

    /** Operador de salida */
    friend ostream &operator<<(ostream &os, const Imagen &imagen);

    /** Getters */
    const string &getId() const;
    const string &getNombre() const;
    unsigned int getTam() const;
    const Fecha &getFecha() const;
    Etiqueta *getEtiquetada() const;
    std::string getEtiqueta();

    /** Destructor */
    virtual ~Imagen();
};


#endif //IMAGENES_IMAGEN_H
