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
#include "THashImagen.h"


class ImageBook {
private:
    using email = std::string;

    THashImagen _images;
    list<Etiqueta> _labels;
    map<email ,Usuario> _users;

    friend class Usuario;

    unsigned long djb2(std::string cadena);
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
    /**@brief Crea una lista doblemente enlazada de imagenes que contengan el nombre de la etiqueta
     * pasada por parametro
     * @param etiqueta: nombre de la etiqueta que se busca en la imagen
     * @return lista de imagenes con la etiqueta de nombre @param etiqueta*/
    std::vector<Imagen*> buscarImagEtiq (string etiqueta);
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
    vector<Etiqueta*> getMasLikes();
    /**@brief devuelve la etiqueta con un nombre dado.
     * @param nombreEti: email del usuario que se busca
     * @return puntero al los datos de la etiqueta con nombre*/
    Etiqueta* buscaEtiqueta(std::string nombreEti);
    /**@brief devuelve la etiqueta con un nombre dado.
     * @param nombreEti: email del usuario que se busca
     * @return puntero al los datos de la etiqueta con nombre*/
    vector<Usuario*> buscarUsuarioFechaImagen(Fecha fecha);
    void nuevaImagen(Imagen &img,std::string email);

    float factorCarga(){return _images.factorCarga();}
    unsigned int tamTabla(){return _images.tamTabla();}
    unsigned int maxColisiones(){return _images.maxColisiones();}
    std::string mostrarEstadoTablaImagenes(){return _images.mostrarEstadoTablaImagenes();}

    std::vector<Etiqueta*> top5Etiq();
    std::vector<Usuario*> top3User();

    void borrarImg(std::string id);

};


#endif //IMAGENES_IMAGEBOOK_H
