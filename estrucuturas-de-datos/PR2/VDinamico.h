//
// Created by gabis on 28/09/2022.
//

#ifndef IMAGENES_VDINAMICO_H
#define IMAGENES_VDINAMICO_H

#include <climits>
#include <algorithm>
#include <cmath>

template<typename T>
class VDinamico {
private:
    unsigned int _tamf,_taml;
    T *v;
public:
    /***/
    VDinamico();
    VDinamico(unsigned int taml);
    VDinamico(const VDinamico<T> &origen);
    VDinamico(const VDinamico<T> &origen, unsigned int posicionInicial,unsigned numElementos);
    VDinamico<T> operator=(const VDinamico<T> &asignacion);
    T& operator[](unsigned int pos);
    /**@brief Añade un elemento en cualquier posición del vector desplazando el resto a la derecha
     * @param dato: elemento a añadir
     * @param pos: posición en la que va ser introducido*/
    void insertar(const T& dato, unsigned int pos = UINT_MAX);
    /**@brief Borra un elemento del vector y lo reajusta
     * @param pos: posición del elemento a borrar*/
    T borrar(unsigned int pos =UINT_MAX);
    /**@return tamaño logico del vector*/
    unsigned int tamlog(){return _taml;};
    /**@brief ordena el vector de menor a mayor*/
    void ordenar();
    /**@brief ordena el vector de mayor a menor*/
    void ordenarRev();
    /**@brief busca un dato en el vector
     * @param dato: el dato que quieres buscar
     * @return la posicion en la que se encuentra el dato
     */
    int BusquedaBin(T &dato);
    /**@brief destructor*/
    virtual ~VDinamico();
};

template<typename T>
VDinamico<T>::VDinamico(): _taml(0),_tamf(1) {
    v = new T[_tamf];
}

template<typename T>
VDinamico<T>::VDinamico(unsigned int taml): _taml(taml),_tamf(pow(2,ceil((log2(_taml))))) {
    v = new T[_tamf];
}

template<typename T>
VDinamico<T>::VDinamico(const VDinamico<T> &origen): _tamf(origen._tamf),_taml(origen._taml) {
    v = new T[_tamf];
    for (unsigned int i=0;i<_taml;i++) {
        v[i] = origen.v[i];
    }
}

template<typename T>
VDinamico<T>::VDinamico(const VDinamico<T> &origen, unsigned int posicionInicial, unsigned int numElementos): _taml(numElementos),_tamf(pow(2,ceil((log2(_taml))))) {
    if (posicionInicial>origen._taml-1||origen._taml-posicionInicial<numElementos){
        throw std::out_of_range("VDinamico<T>::VDinamico: Fuera de rango");
    }

    v = new T[_tamf];
    for (unsigned int i=0;i<_taml;i++) {
        v[i] = origen.v[i+posicionInicial];
    }
}

template<typename T>
VDinamico<T> VDinamico<T>::operator=(const VDinamico<T> &asignacion) {
    if(this != &asignacion){
        _tamf = asignacion._tamf;
        _taml = asignacion._taml;
        delete [] v;
        v = new T[_tamf];
        for (unsigned int i = 0; i < _taml; ++i) {
            v[i] = asignacion.v[i];
        }
    }
    return *this;
}

template<typename T>
T& VDinamico<T>::operator[](unsigned int pos) {
    if(pos>_taml-1){
        throw std::out_of_range("VDinamico<T>::operator[]: Fuera de rango");
    }
    return v[pos];
}

/**@todo preguntar y hacer lo de Uint_Max**/
template<typename T>
void VDinamico<T>::insertar(const T &dato, unsigned int pos) {
    if(_taml==_tamf){
        T *vaux;
        vaux= new T[_tamf=_tamf*2];
        for(unsigned int i=0;i<_taml;i++)
            vaux[i]=v[i];
        delete []v;
        v=vaux;
    }
    if(pos == UINT_MAX){
        v[_taml++]=dato;
        return;
    }
    if(pos>_tamf-1){
        throw std::out_of_range("VDinamico<T>::insertar: Fuera de rango");
    }
    for (unsigned int i = _taml; i > pos-1; --i) {
        v[i] = v[i-1];
    }
    v[pos] = dato;
    _taml++;
}

template<typename T>
T VDinamico<T>::borrar(unsigned int pos) {
    if(_taml*3<_tamf){;
        T *vaux = new T[_tamf=_tamf/2];
        for(unsigned int i=0;i<_taml;i++){
            vaux[i]=v[i];
        };
        delete []v;
        v=vaux;
    }
    if(pos != UINT_MAX){
        if(pos>_taml-1){
            throw std::out_of_range("VDinamico<T>::borrar: Fuera de rango");
        }
        T vuelta=v[pos];
        for (unsigned int i = pos; i < _taml; ++i) {
            v[i] = v[i+1];
        }
        --_taml;
        return vuelta;
    }else{
        return v[--_taml];
    }
}

template<typename T>
void VDinamico<T>::ordenar() {
    sort(v,v+_taml);
}

template<typename T>
void VDinamico<T>::ordenarRev() {
    struct MayorMenor{
        bool operator()(T i,T j)
        {return i>j;}
    }comparador;
    sort(v,v+_taml,comparador);
}

/**@todo preguntar lo de crear un objeto T*/
template<typename T>
int VDinamico<T>::BusquedaBin(T &dato) {

    int inf = 0;
    int sup = _taml - 1;
    int media;

    while (inf <= sup) {
        media = (inf + sup) / 2;
        if (v[media] == dato) {
            T aux = v[media];
            return media;
        }else if (v[media] < dato) {inf = media + 1;}
        else sup = media - 1;
    }
    return -1;
}

template<typename T>
VDinamico<T>::~VDinamico() {
    delete [] v;
}


#endif //IMAGENES_VDINAMICO_H
