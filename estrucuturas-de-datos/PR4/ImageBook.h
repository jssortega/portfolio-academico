//
// Created by gabis on 12/10/2022.
//

#ifndef IMAGENES_IMAGEBOOK_H
#define IMAGENES_IMAGEBOOK_H
#include <vector>
#include <list>
#include <map>
#include "Etiqueta.h"
#include "Imagen.h"
#include "Usuario.h"


class ImageBook {
private:
    using email = std::string;

    vector<Imagen> _images;
    list<Etiqueta> _labels;
    map<email ,Usuario> _users;

    friend class Usuario;
public:

    ImageBook(std::string etiquetas,std::string usuarios,std::string imagenes);
    /**@brief Rellena _labels con las etiquetas dadas en el fichero
     * @param fich: fichero con etiquetas*/
    void leerEtiquetas(std::string fich);
    /**@brief Rellena _users con los usuarios dados en el fichero
     * @param fich: fichero con etiquetas*/
    void leerUsuarios(std::string fich);
    /**@brief Rellena _images con los datos de las imagenes dadas en el fichero
     * @param fich: fichero con datos de imagenes*/
    void leerImagenes(std::string fich);
    /**@brief Busca la etiqueta más repetida en el vector _images
     * @return Un string con el nombre de la etiqueta más repetida*/
    std::string etiquetaMasRepetida();
    /**@brief Crea una lista doblemente enlazada de imagenes que contengan el nombre de la etiqueta
     * pasada por parametro
     * @param etiqueta: nombre de la etiqueta que se busca en la imagen
     * @return lista de imagenes con la etiqueta de nombre @param etiqueta*/
    list<Imagen*> buscarImagEtiq (string etiqueta);
    /**@brief devuelve el usuario con un email dado.
     * @param email: email del usuario que se busca
     * @return puntero al los datos de usuario con email @param email*/
    Usuario* buscaUsuario(std::string email){auto it = _users.find(email);  return it != _users.end() ? &it->second : nullptr;}
    /**@brief devuelve la imagen con un id dado.
     * @param id: email del usuario que se busca
     * @return puntero al los datos de la imagen con id @param id*/
    Imagen* buscaImagen(std::string id);
    /**@brief localiza a todos los usuarios que han colgado al menos una
     * imagen con la etiqueta dada.
     * @param etiqueta: nombre de la etiqueta que se busca en el usuario
     * @return lista de usuarios con imagenes de la etiqueta de nombre*/
     vector<Usuario*> buscarUsuarioEtiq (string etiqueta);
    /**@brief devuelve el usuario (o usuarios en caso de empate) más activo
     * en la red porque cuelga más imágenes que el resto.
     * @param etiqueta: nombre de la etiqueta que se busca en el usuario
     * @return lista de usuarios con imagenes de la etiqueta de nombre*/
    vector<Usuario*> getMasActivos ();
    /**@brief devuelve la etiqueta con un nombre dado.
     * @param nombreEti: email del usuario que se busca
     * @return puntero al los datos de la etiqueta con nombre*/
    Etiqueta* buscaEtiqueta(std::string nombreEti);
    /**@brief devuelve la etiqueta con un nombre dado.
     * @param nombreEti: email del usuario que se busca
     * @return puntero al los datos de la etiqueta con nombre*/
    vector<Usuario*> buscarUsuarioFechaImagen(Fecha fecha);
    vector<Usuario*> buscarUsuariosPremium();

};


#endif //IMAGENES_IMAGEBOOK_H
