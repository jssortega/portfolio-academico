//
// Created by gabis on 07/12/2022.
//

#ifndef IMAGENES_MALLAREGULAR_H
#define IMAGENES_MALLAREGULAR_H

#include <list>
#include <vector>
#include "Imagen.h"

template<typename T>
class MallaRegular{
    struct Celda{
        std::list<T> puntos;
        Celda() = default;
        unsigned int insertar(const T& dato){puntos.push_back(dato);return puntos.size();}
        T* buscar(const T& dato){return &*std::find(puntos.begin(),puntos.end(),dato);}
        bool borrar(const T& dato);
        std::list<T> devolverPuntos(){return puntos;};
    };

    std::vector<std::vector<Celda>> _malla;
    float _xMin,_yMin,_xMax,_yMax,_tamCeldaX,_tamCeldaY;
    unsigned int _maxElementosC,_totalElementos;

    Celda* realADiscreto(float x, float y){return &_malla[(y - _yMin) / _tamCeldaY][(x - _xMin) / _tamCeldaX];}

public:
    MallaRegular() = default;
    MallaRegular(float xMin,float yMin,float xMax,float yMax,int nDiv);
    MallaRegular& operator=(MallaRegular&& mr) noexcept ;
    void insertar(float x,float y,const T& dato){unsigned int nElementos = realADiscreto(x,y)->insertar(dato);_maxElementosC = _maxElementosC > nElementos ? _maxElementosC : nElementos;++_totalElementos;}
    T* buscar(float x,float y,const T& dato){return realADiscreto(x,y)->buscar(dato);}
    bool borrar(float x,float y,const T& dato){return realADiscreto(x,y)->borrar(dato);}
    std::vector<T> buscarRango(float rxmin, float rymin, float rxmax, float rymax);
    unsigned int maxElementosPorCelda(){return _maxElementosC;}
    float promedioElementosPorCelda(){return (float)_totalElementos/(_malla.size()*_malla.size());}
    /**@return firts: xMin. second: xMax*/
    pair<float,float> getX(){return pair<float,float>(_xMin,_xMax);}
    /**@return firts: yMin. second: yMax*/
    pair<float,float> getY(){return pair<float,float>(_yMin,_yMax);}
};

template<typename T>
bool MallaRegular<T>::Celda::borrar(const T &dato) {
    auto borrado = std::find(puntos.begin(),puntos.end(),dato);
    if(borrado != puntos.end()){
        puntos.erase(borrado);
        return true;
    }
    return false;
}

template<typename T>
MallaRegular<T>::MallaRegular(float xMin, float yMin, float xMax, float yMax, int nDiv) :
                                _xMin(xMin), _yMin(yMin), _xMax(xMax), _yMax(yMax),_tamCeldaX((xMax - xMin) / nDiv),
                                _tamCeldaY((yMax - yMin) / nDiv), _malla(nDiv+1, vector<Celda>(nDiv+1)),_maxElementosC(0),
                                _totalElementos(0){}

template<typename T>
vector<T> MallaRegular<T>::buscarRango(float rxmin, float rymin, float rxmax, float rymax) {
    vector<T> retorno;

    int a =(rymin - _yMin) / _tamCeldaY;
    int b = (rymax - _yMin) / _tamCeldaY - 1;

    for (int i = (rymin - _yMin) / _tamCeldaY; i <=  (rymax - _yMin) / _tamCeldaY ; ++i) {
        //i = i<0 ? 0 : i;
        for (int j = (rxmin - _xMin) / _tamCeldaX; j <= (rxmax - _xMin) / _tamCeldaX ; ++j) {
            //j = j<0 ? 0 : j;
            Celda cur = _malla[i][j];
            for (auto &punto: cur.puntos) {
                if (punto->getX() < rxmax && punto->getX() > rxmin && punto->getY() < rymax &&
                punto->getY() > rymin) {
                    retorno.push_back(punto);
                }
            }
        }
    }
    return retorno;
}

template<typename T>
MallaRegular<T> &MallaRegular<T>::operator=(MallaRegular &&mr) noexcept {
    _malla = std::move(mr._malla);
    _xMin = mr._xMin;
    _yMin = mr._yMin;
    _xMax = mr._xMax;
    _yMax = mr._yMax;
    _tamCeldaX = mr._tamCeldaX;
    _tamCeldaY = mr._tamCeldaY;
    _maxElementosC = mr._maxElementosC;
    _totalElementos = mr._totalElementos;
    return *this;
}

#endif //IMAGENES_MALLAREGULAR_H
