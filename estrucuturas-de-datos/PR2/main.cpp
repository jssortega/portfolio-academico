/****************************************************
 * @author Gabriel Soria Sánchez gss00016@red.ujaen.es
 * @author Jesús Ortega Castillo joc00023@red.ujaen.es
 ****************************************************/

#include <iostream>
#include "Timer.h"
#include "ImageBook.h"
#include "fecha.h"
#include "Imagen.h"



int main() {

    Timer clock;

    /*******************************************************************************************************
     * Instanciar la clase ImageBook según el diseño UML, rellenando la lista enlazada con las          *
     * etiquetas del fichero etiquetas.txt y el vector dinámico de imágenes como en la práctica         *
     * anterior (exceptuando que ahora la cadena con las etiquetas no forma parte de la clase           *
        * Imagen). Para enlazar cada imagen con una etiqueta, durante la lectura del fichero, se obtiene   *
        * la primera de las etiquetas de cada imagen, se busca dicha etiqueta en la lista de etiquetas (en *
        * ImageBook::labels) y se enlaza mediante la asociación Imagen::                                   *
        ****************************************************************************************************/
    clock.start();
    ImageBook book;
    book.leerEtiquetas("../etiquetas.txt");
    book.leerImagenes("../imagenes_v1.csv");
    clock.stop();
    std::cout << "Tiempo primer apartado: " << clock.getElapsedTimeInMilliSec() << " ms." << std::endl;
    /*************************************************************************************************
     * Devolver y mostrar por pantalla todas aquellas imágenes (id, usuario) con la etiqueta “playa” *
     * y posteriormente las que tengan la etiqueta “comida”.                                         *
     *************************************************************************************************/
    clock.start();
    ListaDEnlazada<Imagen*> lPlaya(book.buscarImagEtiq("playa"));
    ListaDEnlazada<Imagen*> lComida(book.buscarImagEtiq("comida"));
    ListaDEnlazada<Imagen*>::Iterador itImag = lPlaya.iterador();
    std::cout<<"\nPlaya:"<<std::endl;
    while (itImag.haySiguiente()){
        std::cout<<*itImag.dato();
        itImag.siguiente();
    }
    itImag = lComida.iterador();
    std::cout<<"\nComida:"<<std::endl;
    while (itImag.haySiguiente()){
        std::cout<<*itImag.dato();
        itImag.siguiente();
    }
    clock.stop();
    std::cout << "Tiempo segundo apartado: " << clock.getElapsedTimeInMilliSec() << " ms.\n" << std::endl;

    /********************************************************************************************
     * Unir ambas listas resultantes en una nueva lista resultado usando la función concatenar, *
     * comprobando que el resultado es idéntico usando el operator                              *
     ********************************************************************************************/
    clock.start();
    ListaDEnlazada<Imagen*> concatena = lComida.concatena(lPlaya);
    ListaDEnlazada<Imagen*> lUnion = lComida+lPlaya;
    if(lUnion == concatena){
        std::cout << "Iguales";
    } else{
        std::cout << "Diferentes";
    }
    clock.stop();
    std::cout << "\nTiempo tercer apartado: " << clock.getElapsedTimeInMilliSec() << " ms." << std::endl;

    /*********************************************************************************************
     * Devolver cuál de las etiquetas es la más repetida usando el mismo procedimiento anterior. *
     * Para ello iterar sobre todas las etiquetas para posteriormente buscarlas.                 *
     *********************************************************************************************/
    clock.start();
    std::cout <<  '\n' <<book.etiquetaMasRepetida() << std::endl;
    clock.stop();
    std::cout << "Tiempo cuarto apartado: " << clock.getElapsedTimeInMilliSec() << " ms.\n" << std::endl;

    /*******************************************************************************************************
     * medir los tiempos de ejecución de la operación anterior e implementar la primitiva de la lista      *
     * ListaDEnlazada<T>::Iterador busca (T &dato) que devuelve un iterador que referencie a un dato en la *
     * lista igual al suministrado . Utilizarla 1 en el programa principal para localizar la imagen con id *
     * 616564861 de la lista de imágenes obtenidas y, si existiera, mostrar toda su información.           *
     *******************************************************************************************************/
    clock.start();
    Fecha fecha;
    Imagen* imagen = new Imagen("616564861", "", "", 0, fecha, nullptr);
    itImag = lUnion.busca(imagen);
    if(itImag.haySiguiente()) {
        std::cout << "Imagen:(ID=" << itImag.dato()->getId()
                  << " Email=" << itImag.dato()->getEmail() << " Fichero=" << itImag.dato()->getNombre() << " Tam="
                  << itImag.dato()->getTam()
                  << " Fecha=" << itImag.dato()->getFecha().cadenaDia()
                  << " Etiqueta=" << itImag.dato()->getEtiqueta()
                  << ")" << std::endl;
    }
    clock.stop();
    std::cout << "Tiempo quinto apartado: " << clock.getElapsedTimeInMilliSec() << " ms.\n" << std::endl;
    return 0;
}