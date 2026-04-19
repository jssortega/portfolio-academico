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

    int _popularidad;
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

    vector<Imagen*> buscarEtiq(std::string nombreEtiq);

    unsigned int getNumImages(){return _userImages.size();}

    void insertarImagen(Imagen* imagen){_userImages[imagen->getId()] = imagen;}

    void eliminarImagen(std::string id){_userImages.erase(id);}

    void anadirEtiquetaImagen(std::string id, std::string nombreEtiq);

    std::vector<Usuario*> buscarUsuariosEtiq(string nombreEti);

    bool esMasActivo();

    Imagen* getImagenMasAntigua(){imagenFecha(<);}
    Imagen* getImagenMasReciente(){imagenFecha(>);}

    std::vector<Imagen*> getImagenesEtiqueta (string nombreEti);

    void meGustaImagen(Imagen* imagen);

    void likeAutomatico(std::string nombreEtiq);

    int actualizarPopularidad();

    int getPopularidad(){return _popularidad;}

    const string &getEmail() const{return _email;}

    const map<std::string, Imagen *> &getUserImages() const{return _userImages;};
};


#endif //IMAGENES_USUARIO_H
