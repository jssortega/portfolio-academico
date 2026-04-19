//
// Created by gabis on 26/11/2022.
//

#include <valarray>
#include <sstream>
#include "THashImagen.h"

unsigned int THashImagen::hash(unsigned long clave, int intento) {
    return (clave+intento*clave%14713)%_tamMax;
}

THashImagen::THashImagen(int maxElementos, float lambda) : _taml(0),_tamMax(buscarPrimo(maxElementos/lambda)), _lambda(lambda)
                        {_tabla = vector(_tamMax,Dato());}

THashImagen::THashImagen(THashImagen &thash) : _tamMax(thash._tamMax),_lambda(thash._lambda),_tabla(thash._tabla){}

THashImagen THashImagen::operator=(THashImagen &thash) {
    if(this != &thash){
        _tabla = thash._tabla;
        _tamMax = thash._tamMax;
        _taml = thash._taml;
        _lambda = thash._lambda;
        _colisonesMax = thash._colisonesMax;
        _colisionesTotales = thash._colisionesTotales;
        _10co = thash._10co;
    }
    return *this;
}

bool THashImagen::insertar(unsigned long clave, Imagen* imagen) {
    if((float)_taml/_tamMax >= _lambda){
        redispersar(_tamMax*1.3);
    }

    if(!buscar(clave)){
        unsigned int colisiones = 0;

        unsigned int posicion, intento = 0;
        posicion = hash(clave, intento++);
        while (_tabla[posicion].estado == ocupado) {
            ++colisiones;
            posicion = hash(clave, intento++);
        }
        _tabla[posicion] = Dato(imagen, clave);
        ++_taml;

        _colisionesTotales += colisiones;
        if (colisiones > 10) ++_10co;
        _colisonesMax = _colisonesMax < colisiones ? colisiones : _colisonesMax;
        return true;
    }
    return false;
}

Imagen *THashImagen::buscar(unsigned long clave) {
    unsigned int posicion,intento=0;
    posicion = hash(clave,intento++);
    if(_tabla[posicion].estado != ocupado){
        return nullptr;
    }
    while (_tabla[posicion]._clave != clave){
        if(_tabla[posicion].estado != ocupado){
            return nullptr;
        }
        posicion = hash(clave,intento++);
    }
    return _tabla[posicion]._dato;
}

bool THashImagen::borrar(unsigned long clave) {
    unsigned int posicion,intento=0;
    posicion = hash(clave,intento++);
    while (_tabla[posicion]._clave != clave){
        if(_tabla[posicion].estado == libre){
            return false;
        }
        posicion = hash(clave,intento++);
    }
    _tabla[posicion].estado = disponible;
    ++_borrados;
    --_taml;
    return true;
}

std::string THashImagen::mostrarEstadoTablaImagenes() {
    std::stringstream retorno;
    retorno << "Maximo de Colisiones: " << maxColisiones() << "\nVeces con 10 colisones: " << numMax10() << "\nPromedio de colisones: "
            << promedioColisiones() << "\nFactor de carga: " << factorCarga() << "\nTamanno de la tabla: " << tamTabla();
    return retorno.str();
}

unsigned int THashImagen::buscarPrimo(unsigned int n) {
    vector<unsigned int> primos;
    unsigned int p = 0;
    bool esPrimo;
    for (int i = 2; p < n; ++i) {
        esPrimo = true;
        for(auto pr : primos){
            esPrimo = esPrimo && i%pr != 0;
        }
        if(esPrimo) {p = i;
        primos.push_back(p);}
    }
    return p;
}

void THashImagen::redispersar(unsigned int tam) {
    THashImagen nuevo(tam,_lambda);
    for(auto & dato : _tabla){
        if(dato.estado == ocupado) nuevo.insertar(dato._clave,dato._dato);
    }
    *this = nuevo;
}



