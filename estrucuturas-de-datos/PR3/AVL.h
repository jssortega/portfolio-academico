//
// Created by gabis on 25/10/2022.
//

#ifndef IMAGENES_AVL_H
#define IMAGENES_AVL_H

#include <stack>
#include "VDinamico.h"
#include <algorithm>

template <typename T>
class AVL {
private:

    struct Nodo {
    public:
        Nodo* _izq, *_dch;
        T _dato;
        char _bal;
        friend class AVL;
        Nodo(T dato): _izq(nullptr), _dch(nullptr), _bal(0), _dato(dato){}
    };

    Nodo *_raiz;
    unsigned int _tam;

    bool insertar (Nodo* &p, T &dato);

    VDinamico<T*> inorden(Nodo* &p, VDinamico<T*> &vector);

    Nodo* buscarRec(T& dato, Nodo*& nodo);
    /** @brief rota un nodo a la _dch
     * @param nodo: el nodo que se quiere rotar
     */
    void rotDch(Nodo* &nodo);
    /** @brief rota un nodo a la _izq
     * @param nodo: el nodo que se quiere rotar
     */
    void rotIzq(Nodo* &nodo);
    /** @brief inserta un _dato en la posicion que le corresponda
     * @param dato: el _dato que se quiere insertar
     * @return si se ha insertado el _dato
     */

    unsigned int alturaRec(Nodo* raiz){return raiz ? std::max(alturaRec(raiz->_izq), alturaRec(raiz->_dch))+1 : -1;}

public:
    /** @brief constructor por defecto */
    AVL(): _raiz(nullptr), _tam(0) {}
    /** @brief constructor por copia */
    AVL(const AVL<T>& orig){*this = orig;}

    void operator=(const AVL<T>& orig);

    bool inserta(T &dato){return insertar(_raiz,dato);};
    /**@return devuelve el tamaño del arbol*/
    unsigned int numElementos(){return _tam;};

    T* buscaRec(T& dato);

    T* buscaIt(T& dato);

    VDinamico<T*> recorreInorden(){VDinamico<T*> vector; return inorden(_raiz,vector);};

    unsigned int altura(){return alturaRec(_raiz);}

    virtual ~AVL();

};

/** rotaciones*/
template<typename T>
void AVL<T>::rotDch(AVL::Nodo *&nodo) {
    Nodo *q = nodo, *r;
    nodo = q->_izq;
    r = nodo;
    q->_izq = r->_dch;
    nodo->_dch = q;
    q->_bal--;

    if(r->_bal > 0) {
        q->_bal -= r->_bal;
        r->_bal--;
    }
    if(q->_bal < 0)
        r->_bal -= q->_bal;
}

template<typename T>
void AVL<T>::rotIzq(AVL::Nodo *&nodo) {
    Nodo *q = nodo, *r;
    r = q->_dch;
    nodo = r;

    q->_dch = r->_izq;
    r->_izq = q;
    q->_bal++;

    if(r->_bal < 0){
        q->_bal += -r->_bal;
        r->_bal++;
    }
    if(q->_bal > 0)
        r->_bal += q->_bal;
}
/***********************************************************/

/** insertar */
template<typename T>
bool AVL<T>::insertar(AVL::Nodo* &p, T &dato) {
    Nodo *raiz = p;
    bool insertado = false;

    if(!raiz){
        raiz = new Nodo(dato);
        p = raiz;
        _tam++;
        insertado = true;
    }else if(dato < raiz->_dato){
        if(insertar(raiz->_izq, dato)){
            raiz->_bal++;
            if(raiz->_bal == 1)
                insertado = true;
            else if(raiz->_bal == 2){ //caso 1
                if(p->_izq->_bal == -1){
                    rotIzq(raiz->_izq);
                }
                rotDch(p); //roto p y no raiz porque p al tener la referencia trabajo sobre el arbol en sí, raiz es una copia
            }
        }
    }else if(dato > raiz->_dato){
        if(insertar(raiz->_dch, dato)) {
            raiz->_bal--;

            if (raiz->_bal == -1) {
                insertado = true;
            } else if (raiz->_bal == -2) {
                if (p->_dch->_bal == 1) {
                    rotDch(raiz->_dch);
                }
                rotIzq(p);

            }
        }
    }
    return insertado;
}

/**************************************************/

/** busqueda recursiva */
template<typename T>
typename AVL<T>::Nodo *AVL<T>::buscarRec(T &dato, AVL::Nodo *&nodo) {
    if (!nodo){return nullptr;}
    if(nodo->_dato < dato) {return buscarRec(dato, nodo->_dch);}
    if(nodo->_dato > dato) {return buscarRec(dato, nodo->_izq);}
    return nodo;
}

template<typename T>
T *AVL<T>::buscaRec(T &dato) {
    Nodo *encontrado = buscarRec(dato, _raiz);
    if(encontrado) {
        return &encontrado->_dato;
    }
    return nullptr;
}

template<typename T>
T *AVL<T>::buscaIt(T &dato) {
    Nodo* cur = _raiz;
    while(cur->_dato != dato){
        cur = dato < cur->_dato ? cur->_izq : cur->_dch;
    }
    return &cur->_dato;
}

/****************************************************/
template<typename T>
VDinamico<T *> AVL<T>::inorden(AVL::Nodo *&p, VDinamico<T*> &vector) {
    if(p){
        inorden(p->_izq, vector);
        T* auxi = &p->_dato;
        vector.insertar(auxi);
        inorden(p->_dch, vector);
    }
    return vector;
}

template<typename T>
AVL<T>::~AVL() {
    std::stack<Nodo*> pila;
    std::stack<Nodo*> pila2;
    Nodo* cur = _raiz;
    if(cur) pila.push(_raiz);

    while(!pila.empty()){
        cur = pila.top();
        pila2.push(cur);
        pila.pop();
        if(cur->_izq)pila.push(cur->_izq);
        if(cur->_dch)pila.push(cur->_dch);
    }

    while(!pila2.empty()){
        cur = pila2.top();
        pila2.pop();
        delete cur;
    }
    _raiz = nullptr;
    _tam = 0;
}

template<typename T>
void AVL<T>::operator=(const AVL<T> &orig) {
    if(this != &orig){
        this->~AVL();
        std::stack<Nodo*> pila;
        Nodo* cur = orig._raiz;
        if(cur) pila.push(cur);

        while(!pila.empty()){
            cur = pila.top();
            inserta(cur->_dato);
            pila.pop();
            if(cur->_izq)pila.push(cur->_izq);
            if(cur->_dch)pila.push(cur->_dch);
        }
    }
}



/******************************************************************************/

#endif //IMAGENES_AVL_H
