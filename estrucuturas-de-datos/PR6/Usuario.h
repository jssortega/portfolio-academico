//
// Created by gabis on 26/10/2022.
//

#ifndef IMAGENES_USUARIO_H
#define IMAGENES_USUARIO_H

#include <string>
#include <map>
#include <vector>
#include "Imagen.h"
#include <functional>

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
    /** Operadores de comparacion */
    bool operator<(const Usuario &rhs) const;
    bool operator>(const Usuario &rhs) const;
    bool operator<=(const Usuario &rhs) const;
    bool operator>=(const Usuario &rhs) const;
    /** Operadores de equivalencia */
    bool operator==(const Usuario &rhs) const;
    bool operator!=(const Usuario &rhs) const;
    /**@brief busca y devuelve imagenes con una etiqueta de un usuario.
     * @param nombreEtiq: nombre de la etiqueta
     * @return punteros a imagenes que contegan la etiqueta*/
    vector<Imagen*> buscarEtiq(std::string nombreEtiq);
    /**@brief devuelve el número de imagenes de un usuario*/
    unsigned int getNumImages(){return _userImages.size();}
    /**@brief añade una imagen que le relaciona.
     * @param imagen: imagen que le relaciona.*/
    void insertarImagen(Imagen* imagen){_userImages[imagen->getId()] = imagen;}
    /**@brief elimina una imagen que le relaciona.
     * @param id:id de la imagen que le relaciona.*/
    void eliminarImagen(std::string id){_userImages.erase(id);}
    /**@brief añade una etiqueta a una imagen que le relaciona.
     * @param id: id de la imagen a la que añadir una etiqueta.
     * @param nombreEtiq: etiqueta que añade a la imagen.*/
    void anadirEtiquetaImagen(std::string id, std::string nombreEtiq);
    /**@brief busca y devuelve usuarios con una etiqueta en común.
     * @return punteros a usuarios que contegan la etiqueta*/
    std::vector<Usuario*> buscarUsuariosEtiq(string nombreEti);
    /**@brief Comprueba si es el más activo.*/
    bool esMasActivo();
    /**@return Imagen más antigua o más reciente del usuario.*/
    Imagen* getImagenMasAntigua(){imagenFecha(<);}
    Imagen* getImagenMasReciente(){imagenFecha(>);}
    /**@brief busca y devuelve imagenes con una etiqueta en el sistema.
     * @return punteros a imagenes que contegan la etiqueta*/
    std::vector<Imagen*> getImagenesEtiqueta (string nombreEti);
    /**@brief Da like a una imagen del sistema.
     * @param imagen: imagen del sistema.*/
    void meGustaImagen(Imagen* imagen);
    /**@brief Da like a todas las imagenes con la etiqueta del sistema.*/
    void likeAutomatico(std::string nombreEtiq);
    /**@brief Actuliza la popularidad del usuario segun los likes de sus imagenes.
     * @return la popularidad actualizada*/
    const int& actualizarPopularidad();
    /**@return la popularidad actualizada*/
    int getPopularidad() const{return _popularidad;};
    /**@return si userImage contiene o no la imagen de un id*/
    bool contieneImagen(std::string id){return _userImages.find(id) != _userImages.end();}
    /**@brief recorrido sobre user image.
     * @param func: función que se quiere que se ejecute en el recorrido.*/
    void recorrerUserImages(const std::function<bool(pair<const string,Imagen*>&)>& func);

    std::vector<Imagen*> imagenEnZona(float rxmin, float rymin, float rxmax, float rymax);
    void likeAutomaticoZona(float rxmin, float rymin, float rxmax, float rymax);

    const std::string &getEmail() const{return _email;}
};


#endif //IMAGENES_USUARIO_H
