
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
    public:
        Iterador(Nodo* nodo):_nodo(nodo){}

        bool hayAnterior(){return _nodo != nullptr;};
        bool haySiguiente(){return _nodo != nullptr;}
        void anterior(){_nodo = _nodo->_ant;}
        void siguiente(){_nodo = _nodo->_sig;}

        T& operator*(){return _nodo->_dato;};
        T &dato(){return _nodo->_dato;}
    };

    /**Constructor por defecto*/
    ListaDEnlazada();
    /**Constructor copia*/
    ListaDEnlazada(const ListaDEnlazada<T> &orig);
    /**Operador de asignacion*/
    ListaDEnlazada<T> operator=(ListaDEnlazada<T> &asig);
    /**@return elemento que se encuentra al inicio de la lista*/
    T& inicio(){ return _cabecera->_dato;}
    /**@return elemento que se encuentra al final de la lista*/
    T& final(){ return _cola->_dato;}
    /**@return iterador de la lista*/
    Iterador iterador(){return Iterador(_cabecera);}
    /**@brief inserta al comienzo de la lista*/
    void insertarFin(T &dato);
    /**@brief inserta al final de la lista*/
    void insertarInicio(T &dato);
    /**@brief inserta en un punto intermedio de la lista*/
    void insertar(Iterador &i , T& dato );
    /**@brief borra al inicio de la lista*/
    void borrarInicio();
    /**@brief borra al fina de la lista*/
    void borrarFinal();
    /**@brief borra en un punto intermedio de la lista*/
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
    /**Destructor*/
    virtual ~ListaDEnlazada();
};

template<typename T>
ListaDEnlazada<T>::ListaDEnlazada(): _cabecera(nullptr), _cola(nullptr), _tam(0)   {}

template<typename T>
ListaDEnlazada<T>::ListaDEnlazada(const ListaDEnlazada<T> &orig): _cabecera(nullptr), _cola(nullptr), _tam(0) {
    Iterador it(orig._cabecera);
    while (it.haySiguiente()){
        insertarFin(*it);
        it.siguiente();
    }
}

template<typename T>
ListaDEnlazada<T> ListaDEnlazada<T>::operator=(ListaDEnlazada<T> &asig) {
    if(this != &asig){
        while(_tam != 0){
            borrarInicio();
        }
        Iterador it = asig.iterador();
        while (it.haySiguiente()){
            this->insertarFin(*it);
            it.siguiente();
        }
    }
    return *this;
}

template<typename T>
void ListaDEnlazada<T>::insertarFin(T &dato) {
    Nodo* nuevo = new Nodo(dato,_cola, nullptr);

    _cabecera == nullptr ? _cabecera = nuevo : _cola->_sig = nuevo;

    /*if(_cabecera == nullptr){
        _cabecera = nuevo;
    } else{
        _cola->_sig = nuevo;
    }*/
    _cola = nuevo;
    ++_tam;
}

template<typename T>
void ListaDEnlazada<T>::insertarInicio(T &dato) {
    Nodo* nuevo = new Nodo(dato, nullptr, _cabecera);

    _cabecera == nullptr ? _cola = nuevo : _cabecera->_ant = nuevo;

    /*if(_cabecera == nullptr){
        _cola = nuevo;
    } else{
        _cabecera->_ant = nuevo;
    }*/
    _cabecera = nuevo;
    ++_tam;
}

template<typename T>
void ListaDEnlazada<T>::insertar(ListaDEnlazada::Iterador &i, T &dato) {
    if(_cabecera == nullptr || i._nodo == _cabecera || i._nodo == _cola){
        throw std::out_of_range("ListaDEnlazada<T>::insertar: posicion no permitida");
    }

    Nodo *nuevo = new Nodo(dato, i._nodo->_ant,i._nodo);
    if(_cola == nullptr){
        _cola = _cabecera = nuevo;
    }else{
        nuevo->_ant->_sig = nuevo;
        nuevo->_sig->_ant = nuevo;
    }

    ++_tam;
}


template<typename T>
void ListaDEnlazada<T>::borrarInicio() {
    if(_cabecera == nullptr){
        throw std::string("ListaDEnlazada<T>::borrarInicio: No existen elementos");
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
        throw std::string("ListaDEnlazada<T>::borrarInicio: No existen elementos");
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
    if(_cabecera == nullptr || i._nodo == _cabecera || i._nodo == _cola){
        throw std::out_of_range("ListaDEnlazada<T>::borrar: posicion no permitida");
    }
    if(_cabecera==_cola){
        delete i._nodo;
        _cabecera = _cola = nullptr;
    }else{
        i._nodo->_ant->_sig = i._nodo->_sig;
        i._nodo->_sig->_ant = i._nodo->_ant;
        delete i._nodo;
    }
    --_tam;
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
    Iterador it(_cabecera);
    if constexpr (std::is_same<sinPuntero,T>::value){
        while(it.haySiguiente()){
            if(*it == dato){
                break;
            } else {
                it.siguiente();
            }
        }
    }else {
        while (it.haySiguiente()) {
            if (**it == *dato) {
                break;
            } else {
                it.siguiente();
            }
        }
    }
    return it;
}

template<typename T>
ListaDEnlazada<T>::~ListaDEnlazada() {
    while (_tam != 0){
        borrarInicio();
    }
}

template<typename T>
bool ListaDEnlazada<T>::operator==(const ListaDEnlazada<T> &l) {
    if(_tam != l._tam){
        return false;
    }
    Iterador it1(_cabecera);
    Iterador it2(l._cabecera);
    while (it1.haySiguiente()){
        if(*it1 != *it2){
            return false;
        }
        it1.siguiente();
        it2.siguiente();
    }
    return true;
}


#endif //IMAGENES_LISTADENLAZADA_H