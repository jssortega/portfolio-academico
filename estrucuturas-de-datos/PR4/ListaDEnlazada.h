
#ifndef IMAGENES_LISTADENLAZADA_H
#define IMAGENES_LISTADENLAZADA_H

#include <type_traits>



template<typename T>
class ListaDEnlazada{
private:
    struct Nodo{
        T _dato;
        Nodo* _ant,*_sig;

        Nodo():_ant(nullptr),_sig(nullptr),_dato(NULL){};
        Nodo(T &aDato, Nodo *aAnt, Nodo *aSig): _dato(aDato), _ant(aAnt), _sig(aSig){}
    };

    Nodo* _cabecera,*_cola;
    unsigned int _tam;
public:
    class Iterador{
    private:
        Nodo* _nodo;
        friend class ListaDEnlazada;
    public:
        Iterador(Nodo* nodo):_nodo(nodo){}

        bool hayAnterior(){return _nodo != nullptr;};
        bool haySiguiente(){return _nodo != nullptr;}
        void anterior(){_nodo = _nodo->_ant;}
        void siguiente(){_nodo = _nodo->_sig;}

        T& operator*(){return _nodo->_dato;};
        T &dato(){return _nodo->_dato;}
    };


    ListaDEnlazada();

    ListaDEnlazada(const ListaDEnlazada<T> &orig);

    ListaDEnlazada<T> operator=(ListaDEnlazada<T> &asig);

    T& inicio(){ return _cabecera->_dato;}

    T& final(){ return _cola->_dato;}

    Iterador iterador(){return Iterador(_cabecera);}
    /**@brief inserta al comienzo de la lista*/
    void insertarFin(T &dato);
    /**@brief inserta al final de la lista*/
    void insertarInicio(T &dato);
    /**@brief inserta en un punto intermedio de la lista y mueve el iterador al elemento añadido.
     * Si la lista esta vacia o señala el primer elemento se coloca en la primera posición*/
    void insertar(Iterador &i , T& dato );
    /**@brief borra al inicio de la lista*/
    void borrarInicio();
    /**@brief borra al fina de la lista*/
    void borrarFinal();
    /**@brief borra en un punto intermedio de la lista y mueve el iterador al siguiente.
     * Si apunta al último elemento el iterador apuntará al final igual para el principio*/
    void borrar(Iterador &i);
    /**@return cantidad de elementos de la lista*/
    int tam(){return _tam;}
    /**@brief concatena dos listas
     * @return lista formada por la union de dos listas*/
    ListaDEnlazada<T> concatena(const ListaDEnlazada<T> &l);
    ListaDEnlazada<T> operator+(const ListaDEnlazada<T> &l);
    /**@brief busca un elmento en la lista
     * @return iterador apuntando al elemento pedido*/
    Iterador busca(T& dato);

    bool operator==(const ListaDEnlazada<T> &l);

    virtual ~ListaDEnlazada();
};

template<typename T>
ListaDEnlazada<T>::ListaDEnlazada(): _cabecera(nullptr), _cola(nullptr), _tam(0)   {}

template<typename T>
ListaDEnlazada<T>::ListaDEnlazada(const ListaDEnlazada<T> &orig): _cabecera(nullptr), _cola(nullptr), _tam(0) {
    Nodo* cur = orig._cabecera;
    while (cur != nullptr){
        insertarFin(cur->_dato);
        cur = cur->_sig;
    }
}

template<typename T>
ListaDEnlazada<T> ListaDEnlazada<T>::operator=(ListaDEnlazada<T> &asig) {
    if(this != &asig){
        while(_tam != 0){
            borrarInicio();
        }
        Nodo* cur = asig._cabecera;
        while (cur != nullptr){
            this->insertarFin(cur->_dato);
            cur = cur->_sig;
        }
    }
    return *this;
}

template<typename T>
void ListaDEnlazada<T>::insertarFin(T &dato) {
    Nodo* nuevo = new Nodo(dato,_cola, nullptr);

    _cabecera == nullptr ? _cabecera = nuevo : _cola->_sig = nuevo;

    _cola = nuevo;
    ++_tam;
}

template<typename T>
void ListaDEnlazada<T>::insertarInicio(T &dato) {
    Nodo* nuevo = new Nodo(dato, nullptr, _cabecera);

    _cabecera == nullptr ? _cola = nuevo : _cabecera->_ant = nuevo;

    _cabecera = nuevo;
    ++_tam;
}

template<typename T>
void ListaDEnlazada<T>::insertar(ListaDEnlazada::Iterador &i, T &dato) {
    if (_cabecera == nullptr || i._nodo->_ant == nullptr) {
        insertarInicio(dato);
        i = Iterador(_cabecera);
    } else {

        Nodo *nuevo = new Nodo(dato, i._nodo->_ant, i._nodo);
        if (_cola == nullptr) {
            _cola = _cabecera = nuevo;
        } else {
            nuevo->_ant->_sig = nuevo;
            nuevo->_sig->_ant = nuevo;
        }
        i.anterior();
        ++_tam;
    }

}


template<typename T>
void ListaDEnlazada<T>::borrarInicio() {
    if(_cabecera == nullptr){
        throw std::domain_error("ListaDEnlazada<T>::borrarInicio: No existen elementos");
    }

    if(_cabecera == _cola){
        delete _cabecera;
        _cabecera = nullptr;
        _cola = nullptr;
    } else{
        _cabecera = _cabecera->_sig;
        delete _cabecera->_ant;
        _cabecera->_ant = nullptr;
    }
    --_tam;
}

template<typename T>
void ListaDEnlazada<T>::borrarFinal() {
    if(_cabecera == nullptr){
        throw std::domain_error("ListaDEnlazada<T>::borrarInicio: No existen elementos");
    }

    if(_cabecera == _cola){
        delete _cabecera;
        _cabecera = _cola = nullptr;
    } else{
        _cola = _cola->_ant;
        delete _cola->_sig;
        _cola->_sig = nullptr;
    }
    --_tam;
}

template<typename T>
void ListaDEnlazada<T>::borrar(ListaDEnlazada::Iterador &i) {
    if(_cabecera == nullptr){
        throw std::domain_error("ListaDEnlazada<T>::borrar: No existen elementos");
    }

    if(i._nodo == _cola || i._nodo == _cabecera){
        if(i._nodo == _cola){
            borrarFinal();
            i = Iterador(_cola);
        }else if(i._nodo == _cabecera){
            borrarInicio();
            i = Iterador(_cabecera);
        }
    }else {

        if (_cabecera == _cola) {
            delete i._nodo;
            _cabecera = _cola = nullptr;
        } else {
            Nodo *borrado = i._nodo;
            i._nodo->_ant->_sig = i._nodo->_sig;
            i._nodo->_sig->_ant = i._nodo->_ant;
            i.siguiente();
            delete borrado;
        }
        --_tam;
    }
}

template<typename T>
ListaDEnlazada<T> ListaDEnlazada<T>::concatena(const ListaDEnlazada<T> &l) {
    return *this + l;
}

template<typename T>
ListaDEnlazada<T> ListaDEnlazada<T>::operator+(const ListaDEnlazada<T> &l) {
    ListaDEnlazada<T> retorno(*this);
    ListaDEnlazada<T> parte(l);
    parte._cabecera->_ant = retorno._cola;
    retorno._cola->_sig = parte._cabecera;
    retorno._cola = parte._cola;
    parte._tam = 0;
    retorno._tam += l._tam;
    return retorno;
}

template<typename T>
typename ListaDEnlazada<T>::Iterador ListaDEnlazada<T>::busca(T &dato) {
    using sinPuntero = typename std::remove_pointer<T>::type;
    Nodo* cur = _cabecera;
    if constexpr (std::is_same<sinPuntero,T>::value){
        while(cur != nullptr){
            if(cur->_dato == dato){
                break;
            } else {
                cur = cur->_sig;
            }
        }
    }else {
        while (cur != nullptr) {
            if (*cur->_dato == *dato) {
                break;
            } else {
                cur = cur->_sig;
            }
        }
    }
    return Iterador(cur);
}

template<typename T>
bool ListaDEnlazada<T>::operator==(const ListaDEnlazada<T> &l) {
    if(_tam != l._tam){
        return false;
    }
    Nodo* cur1 = _cabecera;
    Nodo* cur2 = l._cabecera;
    while (cur1 == nullptr){
        if(cur1->_dato != cur2->_dato){
            return false;
        }
        cur1 = cur1->_sig;
        cur2 = cur2->_sig;
    }
    return true;
}

template<typename T>
ListaDEnlazada<T>::~ListaDEnlazada() {
    while (_tam != 0){
        borrarInicio();
    }
}




#endif //IMAGENES_LISTADENLAZADA_H