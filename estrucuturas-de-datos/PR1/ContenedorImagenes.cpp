//
// Created by admin on 20/09/2022.
//

#include "ContenedorImagenes.h"
#include <stdexcept>
#include <algorithm>


ContenedorImagenes::ContenedorImagenes() {
    _tamMax = 100;
    _imagenes = new Imagen[_tamMax];
}

ContenedorImagenes::ContenedorImagenes(unsigned int tamMax) : _tamMax(tamMax) {
    _imagenes = new Imagen[_tamMax];
}

ContenedorImagenes::ContenedorImagenes(const ContenedorImagenes &origen): _tamMax(origen._tamMax){
    _imagenes = new Imagen[_tamMax];
    for(int i=0;i<_tamMax;i++){
        _imagenes[i] = origen._imagenes[i];
    }
}

ContenedorImagenes::ContenedorImagenes(const ContenedorImagenes &origen, unsigned int posicionInicial, unsigned int numElementos): _tamMax(numElementos) {
    if(numElementos>_tamMax){
        throw std::out_of_range("ContenedorImagenes::ContenedorImagenes: Fuera de rango");
    }
    _imagenes = new Imagen[numElementos];
    for (int i = 0; i < numElementos; i++) {
        _imagenes[i] = origen._imagenes[posicionInicial+i];
    }
}

ContenedorImagenes ContenedorImagenes::operator=(const ContenedorImagenes &asignacion) {
    if (this != &asignacion){
        _tamMax = asignacion._tamMax;
        delete[] _imagenes;
        _imagenes = new Imagen[_tamMax];
        for(int i=0;i<_tamMax;i++){
            _imagenes[i] = asignacion._imagenes[i];
        }
    }
    return *this;
}

void ContenedorImagenes::asigna(const Imagen &dato, unsigned int pos) {
    if(pos>_tamMax)
        throw std::out_of_range("ContenedorImagenes::asigna: Posicion fuera del rango del contenedor");

    _imagenes[pos] = dato;
}

Imagen ContenedorImagenes::recupera(unsigned int pos) {
    if(pos>tam())
        throw std::out_of_range("ContenedorImagenes::recupera: Posicion sin datos");

    return _imagenes[pos];
}

void ContenedorImagenes::ordenar() {
    sort(_imagenes,_imagenes+_tamMax);
}

void ContenedorImagenes::ordenarRev() {
    //Creo el comparador
    struct MayorAMenor {
        bool operator()(Imagen i, Imagen j) { return (i > j);}
    } mayorAMenor;

    sort(_imagenes,_imagenes+_tamMax,mayorAMenor);
}

unsigned int ContenedorImagenes::tam() {
    int validas=0;
    for (int i = 0; i < _tamMax; ++i) {
        if (_imagenes[i].getId()!=""){
            validas++;
        }
    }
    return validas;
}

ContenedorImagenes::~ContenedorImagenes() {
    delete[] _imagenes;
}












