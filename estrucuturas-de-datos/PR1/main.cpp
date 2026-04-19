/****************************************************
 * @author Gabriel Soria Sánchez gss00016@red.ujaen.es
 * @author Jesús Ortega Castillo joc00023@red.ujaen.es
 ****************************************************/

#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include "Timer.h"
#include "ContenedorImagenes.h"
#include "VDinamico.h"

const int TAM_GENERAL= 10000;

void mostrarInf(VDinamico<Imagen> &imagenes,int cantidadImagenes){
    for (int i = 0; i < cantidadImagenes; ++i) {
        std::cout << imagenes[i];
    }
}

void buscarId(VDinamico<Imagen> &imagenes,string id){
    VDinamico<string> vaux;
    for (int i = 0; i < imagenes.tamlog(); ++i) {
        vaux.insertar(imagenes[i].getId(), i);
    }

    vaux.ordenar();

    if(vaux.BusquedaBin(id) !=-1)
        std::cout << "La posion es: " <<vaux.BusquedaBin(id) << std::endl;
    else {
        std::cout << "El id no existe." << std::endl;
    }

}

VDinamico<Imagen> localizarImagenesUsuario(VDinamico<Imagen> &imagenes, string usuario){
    VDinamico<Imagen> imagenesDeUsuario;
/** @todo porque no vaaaa*/
    for(int i=0;i<imagenes.tamlog();i++){
        if(imagenes[i].getEmail() == usuario){
            imagenesDeUsuario.insertar(imagenes.borrar(i--));
        }
    }
    return imagenesDeUsuario;
}



int main() {
    std::ifstream is;
    std::stringstream  columnas;
    std::string fila;
    int contador=0;
    VDinamico<Imagen> imagenContenedor;
    Fecha fecha;

    std::string id = "";
    std::string email="";
    std::string nombre;
    int tam = 0;
    int dia = 0;
    int mes = 0;
    int anno = 0;
    std::string etiquetas="";

    is.open("../imagenes_v1.csv"); //carpeta de proyecto
    if ( is.good() ) {
        while ( getline(is, fila ) ) {

            //¿Se ha leído una nueva fila?
            if (fila!="") {

                columnas.str(fila);

                //formato de fila: id;email;nombre;tam;fecha;etiquetas

                getline(columnas, id, ';'); //leemos caracteres hasta encontrar y omitir ';'
                getline(columnas,email,';');
                getline(columnas,nombre,';');

                columnas >> tam;   //las secuencia numéricas se leen y trasforman directamente
                columnas.ignore(); //omitimos carácter ';' siguiente

                columnas >> dia; columnas.ignore();
                columnas >> mes; columnas.ignore();
                columnas >> anno; columnas.ignore();

                getline(columnas,etiquetas,';');

                fila="";
                columnas.clear();

                fecha.asignarDia(dia,mes,anno);
                Imagen imagen(id, email, nombre, tam, fecha, etiquetas);

                imagenContenedor.insertar(imagen,contador++);
            }
        }
        is.close();
    } else {
        std::cout << "Error de apertura en archivo" << std::endl;
    }



    std::fstream salida("../Tiempos.txt",std::ifstream::binary|std::ios::in|std::ios::app);
    Timer clock;
    if(!salida.fail()) {
        salida.seekg (0, salida.end);
        int n = salida.tellg();
        n = n/173+1;
        salida<< n << "ª ejecución del programa\n"<<endl;

        /***************************************************************************************************
         * Ordenar el contenedor al revés, es decir, de mayor a menor y mostrar los identificadores de las *
         * primeras 50 imágenes.                                                                           *
         ***************************************************************************************************/
        clock.start();
        imagenContenedor.ordenarRev();
        mostrarInf(imagenContenedor, 50);
        clock.stop();
        salida << "Tiempo primer apartado: " << clock.getElapsedTimeInMilliSec() << " ms." << std::endl;

        /*************************************************************************************************
         * Ordenar el vector de menor a mayor y mostrar los identificadores de las primeras 50 imágenes. *
         *************************************************************************************************/
        clock.start();
        imagenContenedor.ordenar();
        mostrarInf(imagenContenedor, 50);
        clock.stop();
        salida << "Tiempo segundo apartado: " << clock.getElapsedTimeInMilliSec() << " ms." << std::endl;

        /************************************************************************************************
         * Una vez ordenado el vector, buscar imágenes con los identificadores 346335905, 999930245,    *
         * 165837, 486415569 y 61385551, mostrando su posición en el contenedor. Teniendo en cuenta que *
         * pueden no existir                                                                            *
         ************************************************************************************************/
        clock.start();
        buscarId(imagenContenedor, "346335905");
        buscarId(imagenContenedor, "999930245");
        buscarId(imagenContenedor, "165837");
        buscarId(imagenContenedor, "486415569");
        buscarId(imagenContenedor, "61385551");
        clock.stop();
        salida << "Tiempo tercer apartado: " << clock.getElapsedTimeInMilliSec() << " ms." << std::endl;

        /******************************************************************************************************
         * El usuario magdalen_upton99@gmail.com desea descargarse y eliminar sus imágenes del                *
         * sistema. Pasar y borrar todas sus fotos del vector dinámico a un nuevo vector dinámico específico  *
         * para enviárselas. Mostrar el tamaño lógico de ambos vectores y toda la información de las primeras *
         * 10 imágenes que se le enviarán. Si se usan vectores auxiliares, deberán declararse como VDinamico. *
         ******************************************************************************************************/
        clock.start();
        VDinamico<Imagen> contenedorUsuario(localizarImagenesUsuario(imagenContenedor, "magdalen_upton99@gmail.com"));
        std::cout << "Tamanio logico del contenedor general: " << imagenContenedor.tamlog() << std::endl;
        std::cout << "Tamanio logico del contenedor del usuario: " << contenedorUsuario.tamlog() << std::endl;
        mostrarInf(imagenContenedor, 10);
        mostrarInf(contenedorUsuario, 10);
        clock.stop();
        salida << "Tiempo cuarto apartado: " << clock.getElapsedTimeInMilliSec() << " ms.\n" << std::endl;

        /**************************************
         * estudiar los tiempos de los cuatro *
         * apartados anteriores               *
         **************************************/
        //Se encuentra en el archivo Tiempos.txt tras la ejecución
        salida.close();
    }



}