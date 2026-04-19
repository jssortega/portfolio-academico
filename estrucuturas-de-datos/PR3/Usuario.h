//
// Created by gabis on 26/10/2022.
//

#ifndef IMAGENES_USUARIO_H
#define IMAGENES_USUARIO_H

#include <string>
#include "VDinamico.h"
#include "Imagen.h"

class Usuario {
    std::string _email;
    VDinamico<Imagen*> userImages;
public:
    Usuario();
    Usuario(std::string email);

    bool operator<(const Usuario &rhs) const;

    bool operator>(const Usuario &rhs) const;

    bool operator<=(const Usuario &rhs) const;

    bool operator>=(const Usuario &rhs) const;

    bool operator==(const Usuario &rhs) const;

    bool operator!=(const Usuario &rhs) const;

    VDinamico<Imagen*> buscarEtiq(std::string etiq);
    unsigned int getNumImages(){return userImages.tamlog();}
    void insertarImagen(Imagen* imagen){userImages.insertar(imagen);};

    const string &getEmail() const{return _email;}

    const VDinamico<Imagen *> Images() const{return userImages;}

};


#endif //IMAGENES_USUARIO_H
