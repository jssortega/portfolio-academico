//
// Created by gabis on 26/10/2022.
//

#ifndef IMAGENES_USUARIO_H
#define IMAGENES_USUARIO_H

#include <string>
#include <map>
#include <vector>
#include "Imagen.h"

#define  imagenFecha(comp) \
    Imagen* buscada = _userImages.begin()->second;\
    for (auto & image : _userImages) {\
    buscada = image.second->getFecha() comp buscada->getFecha() ? image.second : buscada;\
    }\
    return buscada\

class ImageBook;

class Usuario {
    using id = std::string;

    std::string _email;
    map<id ,Imagen*> _userImages;
    ImageBook* _linkIB;
public:
    Usuario();
    Usuario(std::string email,ImageBook* link);

    bool operator<(const Usuario &rhs) const;

    bool operator>(const Usuario &rhs) const;

    bool operator<=(const Usuario &rhs) const;

    bool operator>=(const Usuario &rhs) const;

    bool operator==(const Usuario &rhs) const;

    bool operator!=(const Usuario &rhs) const;

    vector<Imagen*> buscarEtiq(std::string nombreEtiq, Usuario& user);

    unsigned int getNumImages(){return _userImages.size();}

    void insertarImagen(Imagen* imagen){_userImages[imagen->getId()] = imagen;}

    void anadirEtiquetaImagen(std::string id, std::string nombreEtiq);

    vector<Usuario*> buscarUsuariosEtiq(string nombreEti);

    Imagen* buscarImagen(std::string id){return &*_userImages.find(id)->second;}

    bool esMasActivo();

    Imagen* getImagenMasAntigua(){imagenFecha(<);}
    Imagen* getImagenMasReciente(){imagenFecha(>);}

    const string &getEmail() const{return _email;}

    const map<std::string, Imagen *> &getUserImages() const{return _userImages;};
};


#endif //IMAGENES_USUARIO_H
