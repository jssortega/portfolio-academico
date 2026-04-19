//
// Created by gabis on 26/11/2022.
//

#ifndef IMAGENES_THASHIMAGEN_H
#define IMAGENES_THASHIMAGEN_H
#include "Imagen.h"

class THashImagen {
    enum Estado{disponible,libre,ocupado};
    struct Dato{
        Estado estado = libre;
        unsigned long _clave = 0;
        Imagen* _dato;
        Dato():_dato(){}
        Dato(Imagen* dato,unsigned long clave):_clave(clave), _dato(dato),estado(ocupado){}
    };

    std::vector<Dato> _tabla;
    unsigned int _tamMax;
    unsigned int _taml;
    unsigned int _colisonesMax = 0;
    unsigned int _10co = 0;
    unsigned int _colisionesTotales = 0;
    unsigned int _borrados = 0;
    float _lambda;

    unsigned int hash(unsigned long clave, int intento);
    unsigned int buscarPrimo(unsigned int n);

public:
    THashImagen(int maxElementos, float lambda=0.7);
    THashImagen(THashImagen &thash);
    THashImagen operator=(THashImagen &thash);
    bool insertar(unsigned long clave, Imagen* imagen);
    Imagen * buscar(unsigned long clave);
    bool borrar(unsigned long clave);
    unsigned int numImages(){return _taml;}
    void redispersar(unsigned tam);

    /**Parte 1*/
    unsigned int maxColisiones(){return _colisonesMax;}
    unsigned int numMax10(){return _10co;}
    float promedioColisiones(){return _colisionesTotales/(float)(_taml+_borrados);}
    float factorCarga(){return _lambda;}
    unsigned int tamTabla(){return _tamMax;}
    std::string mostrarEstadoTablaImagenes();


    virtual ~THashImagen() = default;
};


#endif //IMAGENES_THASHIMAGEN_H
