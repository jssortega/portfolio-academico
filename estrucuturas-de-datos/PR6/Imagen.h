//
// Created by admin on 20/09/2022.
//

#ifndef IMAGENES_IMAGEN_H
#define IMAGENES_IMAGEN_H
#include <string>
#include <ostream>
#include <deque>
#include "fecha.h"
#include "Etiqueta.h"
#include "UTM.h"

class Imagen {
private:
    std::string _id;
    std::string _nombre;
    unsigned int _tam;
    int _likes;
    Fecha _fecha;
    UTM pos;
    std::deque<Etiqueta*>_etiquetada;
public:
    /** Cosntructor por defecto */
    Imagen();

    /** Constructor parametrizado */
    Imagen(string _id, string _nombre, unsigned int _tam, const Fecha &_fecha,int likes,float x,float y,const std::deque<Etiqueta*> & etiquetada);
    Imagen(string _id, string _nombre, unsigned int _tam, int dia,int mes,int anno,int likes,float x,float y);

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
    Fecha &getFecha();
    int getLikes(){return _likes;}

    const deque<Etiqueta *> &getEtiquetada() const;
    /** @brief añade etiqueta a etiquetada*/
    void anadirEtiqueta(Etiqueta* etiq){etiq->nuevaImagen(this);_etiquetada.push_back(etiq);};

    float getX(){return pos.GetLongitud();}
    float getY(){return pos.GetLatitud();}

    bool contieneEtiqueta(std::string nombre);

    void nuevoLike(){++_likes;};
    /** Destructor */
    virtual ~Imagen();
};


#endif //IMAGENES_IMAGEN_H
