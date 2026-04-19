//
// Created by gabis on 12/10/2022.
//

#include <sstream>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <ctime>
#include "ImageBook.h"
#include "fecha.h"
#include "img.cpp"

ImageBook::ImageBook(std::string&& etiquetas,std::string&& usuarios,std::string&& imagenes){
    leerEtiquetas(etiquetas);
    leerUsuarios(usuarios);
    leerImagenes(imagenes);
}

void ImageBook::leerEtiquetas(const std::string & fich) {
    std::ifstream entrada(fich);
    std::string nombre;
    if(entrada.good()){
        while(getline(entrada,nombre)){
            Etiqueta label(nombre);
            _labels.push_back(label);
        }
        entrada.close();
    }else{
        throw std::invalid_argument ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
}

void ImageBook::leerUsuarios(const std::string& fich) {
    std::ifstream entrada(fich);
    std::string email;
    if(entrada.good()){
        while(getline(entrada,email)){
            _users[email] = Usuario(email,this);
            if(email[0] == 'e'){
                srand(time(NULL));
                nuevaImagen(Imagen("5234522","etesech",10,1,1,2022,0,(rand()%310000+290000)/10000.0,-(rand()%760000+740000)/10000.0),email);
                _labels.push_back(Etiqueta("#JaenPlazaPlay5"));
                _images.find("5234522")->second->anadirEtiqueta(&*std::find(_labels.begin(),_labels.end(),Etiqueta("#JaenPlazaPlay5")));
            }
        }
        entrada.close();
    }else{
        throw std::invalid_argument ("ImageBook::leerUsuarios: Error apertura del fichero");
    }
}

void ImageBook::leerImagenes(const std::string& fich) {
    std::ifstream entrada;
    std::stringstream  columnas,etiquetasStream;
    std::string fila;

    Fecha fecha;
    std::string id = "";
    std::string email="";
    std::string nombre;
    std::string etiquetaStr;
    Etiqueta etiqueta;
    std::deque<Etiqueta*> etiquetas;
    Etiqueta* etiquetaPtr;
    int tam,dia,mes,anno;
    float latitud,longitud,yMax,xMax,yMin,xMin;
    xMin = yMin = 100;
    yMax = INT16_MIN;

    entrada.open(fich);
    if ( entrada.good() ) {
        while ( getline(entrada, fila ) ) {
            if (!fila.empty()) {

                columnas.str(fila);

                getline(columnas, id, ';');
                getline(columnas,email,';');
                getline(columnas,nombre,';');

                columnas >> tam;
                columnas.ignore();
                columnas >> dia; columnas.ignore();
                columnas >> mes; columnas.ignore();
                columnas >> anno; columnas.ignore();

                getline(columnas,etiquetaStr,';');
                etiquetasStream.str(etiquetaStr);
                etiquetas.clear();
                while (getline(etiquetasStream,etiquetaStr,',')){
                    etiqueta = Etiqueta(etiquetaStr);
                    list<Etiqueta>::iterator itEtiq = std::find(_labels.begin(), _labels.end(), etiqueta);
                    itEtiq != _labels.end() ? etiquetaPtr = &(*itEtiq) : etiquetaPtr = nullptr;
                    etiquetas.push_back(etiquetaPtr);
                }

                columnas >> longitud; columnas.ignore();
                columnas >> latitud; columnas.ignore();


                yMax = yMax < latitud ? latitud : yMax;
                xMax = xMax < longitud ? longitud : xMax;
                yMin = yMin > latitud ? latitud : yMin;
                xMin = xMin > longitud ? longitud : xMin;

                fila="";
                etiquetasStream.clear();
                columnas.clear();

                fecha.asignarDia(dia,mes,anno);
                Imagen* imagen = new Imagen(id, nombre, tam, fecha,id[id.length()-1]-48+(id[id.length()-2]-48)*10+(id[id.length()-3]-48)*100,
                                            longitud,latitud,etiquetas);

                _images[id] = imagen;
                for(auto etiqueta : etiquetas){
                    etiqueta->nuevaImagen(_images.find(id)->second);
                }
                _users.at(email).insertarImagen(_images.find(id)->second);
            }
        }
        entrada.close();
    } else {
        throw std::invalid_argument ("ImageBook::leerEtiquetas: Error apertura del fichero");
    }
    _imagesPos = std::move(MallaRegular<Imagen*>(xMin, yMin, xMax, yMax, 20));
    for(auto & image : _images){
        _imagesPos.insertar(image.second->getX(),image.second->getY(),image.second);
    }
}

std::vector<Imagen*> ImageBook::buscarImagEtiq(std::string etiqueta) {
    auto etiq = std::find(_labels.begin(),_labels.end(),Etiqueta(etiqueta));
    return etiq != _labels.end() ? vector<Imagen*>():etiq->getImages();
}

Imagen *ImageBook::buscaImagen(const std::string& id) {
    return _images.find(id)->second;
}

vector<Usuario *> ImageBook::buscarUsuarioEtiq(std::string etiqueta) {
    vector<Usuario *> retorno;
    bool premisa;
    for(auto & user : _users){
        premisa = false;
        user.second.recorrerUserImages([&](auto userImage){
            for (auto & _etiqueta: userImage.second->getEtiquetada()) {
                if(_etiqueta->getNombre() == etiqueta){
                    retorno.push_back(&user.second);
                    premisa = true;
                    break;
                }
            }
            return premisa;
        });
    }

    return retorno;
}

vector<Usuario *> ImageBook::getMasActivos() {
    vector<Usuario*> retorno;
    for(auto & user : _users){
        if(retorno.size() == 0 || retorno[0]->getNumImages() < user.second.getNumImages()){
            retorno.clear();
            retorno.push_back(&user.second);
        }else if(retorno[0]->getNumImages() == user.second.getNumImages()){
            retorno.push_back(&user.second);
        }
    }
    return retorno;
}

Etiqueta *ImageBook::buscaEtiqueta(const std::string& nombreEti) {
    for (auto & label : _labels) {
        if(label.getNombre() == nombreEti) return &label;
    }
    return nullptr;
}

vector<Usuario *> ImageBook::buscarUsuarioFechaImagen(Fecha fecha) {
    vector<Usuario*> retorno;
    for(auto & user : _users){
        user.second.recorrerUserImages([&](auto userImage){
            if(userImage.second->getFecha().cadenaDia() == fecha.cadenaDia()) {
                retorno.push_back(&user.second);
                return true;
            }
            return false;
        });
    }
    return retorno;
}

vector<Etiqueta *> ImageBook::getMasLikes() {
    vector<Etiqueta*> retorno;
    for(auto & etiqueta : _labels){
        if(retorno.size() == 0 || retorno[0]->getTotalLikes() < etiqueta.getTotalLikes()){
            retorno.clear();
            retorno.push_back(&etiqueta);
        }else if(retorno[0]->getTotalLikes() == etiqueta.getTotalLikes()){
            retorno.push_back(&etiqueta);
        }
    }
    return retorno;
}

void ImageBook::nuevaImagen(const Imagen &img,const std::string& email) {
    _images[img.getId()] = new Imagen(img);
    for(auto etiqueta : img.getEtiquetada()){
        etiqueta->nuevaImagen(_images.find(img.getId())->second);
    }
    _users.at(email).insertarImagen(_images.find(img.getId())->second);
}

std::vector<Etiqueta*> ImageBook::top5Etiq() {
    std::vector<Etiqueta*> retorno(5);
    vector<int> likes(6,0);
    for(auto & etiqueta : _labels){
        likes[0] = etiqueta.getTotalLikes();
        for (int i = 0; i < 5; ++i) {
            if(likes[0]>likes[i+1]){
                retorno[i] = &etiqueta;
                likes[i+1] = likes[0];
                break;
            }
        }
    }
    return retorno;
}

std::vector<Usuario *> ImageBook::top3User() {
    Usuario u = Usuario();
    std::vector<Usuario*> retorno(3,&u);
    int popularidad;
    for(auto & user : _users){
        popularidad = user.second.actualizarPopularidad();
        for (int i = 0; i < 3; ++i) {
            if(popularidad>retorno[i]->getPopularidad()){
                retorno[i] = &user.second;
                break;
            }
        }
    }
    return retorno;
}

void ImageBook::borrarImg(const std::string& id) {
    Imagen* borrar = _images.find(id)->second;
    for(auto & user : buscarUsuarioEtiq(borrar->getEtiquetada()[0]->getNombre())){
        if(user->contieneImagen(id)){
            user->eliminarImagen(id);
        }
    }
    for(auto & etiqueta : borrar->getEtiquetada()){
        etiqueta->eliminarImagen(borrar);
    }
    _images.erase(id);
}

ImageBook::~ImageBook() {
    for(auto & image : _images){
        delete image.second;
    }
}

std::vector<Imagen *> ImageBook::buscarImagEtiLugar(const string& nombre, float rxmin, float rymin, float rxmax, float rymax) {
    std::vector<Imagen*> imagenesRango = _imagesPos.buscarRango(rxmin,rymin,rxmax,rymax);
    std::vector<Imagen*> retorno;
    for(auto & imagen : imagenesRango){
        for(auto & etiqueta : imagen->getEtiquetada()){
            if(etiqueta->getNombre() == nombre){
                retorno.push_back(imagen);
                break;
            }
        }
    }
    return retorno;
}

std::vector<Usuario *> ImageBook::buscarUsuarLugar(float rxmin, float rymin, float rxmax, float rymax) {
    std::vector<Imagen*> imagenesRango = _imagesPos.buscarRango(rxmin,rymin,rxmax,rymax);
    std::vector<Usuario*> retorno;
    for(auto & imagen : imagenesRango){
        for(auto & user : _users){
            if(user.second.contieneImagen(imagen->getId()) && std::find(retorno.begin(), retorno.end(),&user.second) == retorno.end()){
                retorno.push_back(&user.second);
                break;
            }
        }
    }
    return retorno;
}

Etiqueta *ImageBook::buscaEtiquetaRepetida(float rxmin, float rymin, float rxmax, float rymax) {
    std::vector<Imagen*> imagenesRango = _imagesPos.buscarRango(rxmin,rymin,rxmax,rymax);
    Etiqueta* repetida;
    unsigned int mayor = 0;
    unsigned int cur = 0;
    for(auto & etiqueta : _labels){
            for(auto & imagen : imagenesRango){
                auto etiquetasConteo = imagen->getEtiquetada();
                if(std::find(etiquetasConteo.begin(), etiquetasConteo.end(),&etiqueta) != etiquetasConteo.end())++cur;
            }
            if(mayor<cur){
                mayor = cur;
                repetida = &etiqueta;
            }
            cur = 0;
    }
    return repetida;
}

void ImageBook::crearImagenMapa() {
    RGBColor verde(125,255,125);
    Img mapa(600,600,verde);
    pair<float,float> rangoX = _imagesPos.getX();
    float tamX = (rangoX.second-rangoX.first)/600;
    pair<float,float> rangoY = _imagesPos.getY();
    float tamY = (rangoY.second-rangoY.first)/600;
    for(auto & image : _images){
        mapa.pintarPixel((image.second->getX()-rangoX.first)/tamX,(image.second->getY()-rangoY.first)/tamY,255,0,0);
    }
    mapa.guardar("./ImageBook.ppm");
}

Usuario *ImageBook::buscarUsuarioImg(Imagen *imagen) {
    for (auto & user : _users) {
        if(user.second.contieneImagen(imagen->getId())) return &user.second;
    }
    return nullptr;
}






