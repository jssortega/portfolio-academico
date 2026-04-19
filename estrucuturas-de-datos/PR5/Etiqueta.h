//
// Created by gabis on 12/10/2022.
//

#ifndef IMAGENES_ETIQUETA_H
#define IMAGENES_ETIQUETA_H

#include <string>
#include <vector>
#include <algorithm>

class Imagen;

class Etiqueta{
    std::vector<Imagen*> _etiImages;
    std::string _nombre;
public:
    /** Constructor por defecto */
    Etiqueta(): _nombre(""),_etiImages(){}
    /** Constructor copia */
    Etiqueta(std::string nombre): _nombre(nombre),_etiImages(){}

    /** Operadores de equidad */
    bool operator==(const Etiqueta &rhs) const {
        return _nombre == rhs._nombre;
    }
    bool operator!=(const Etiqueta &rhs) const {
        return !(rhs == *this);
    }
    /** Getter */
    std::string getNombre(){return _nombre;};
    std::vector<Imagen*> getImages(){return _etiImages;}

    int getTotalLikes();

    void nuevaImagen(Imagen* imagen){_etiImages.push_back(imagen);}
    void eliminarImagen(Imagen* imagen){auto borrar = std::find(_etiImages.begin(),_etiImages.end(),imagen);_etiImages.erase(borrar);}
};

#endif //IMAGENES_ETIQUETA_H
