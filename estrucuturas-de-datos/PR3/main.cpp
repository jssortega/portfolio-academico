#include <iostream>
#include "Timer.h"
#include "ImageBook.h"
#include <stdlib.h>

#define mostrarInfoImagenUsuario(email) \
    usuario = libro.buscaUsuario(email);\
    imagenes = usuario ? usuario->Images() : VDinamico<Imagen *>();\
    std::cout << "\n" << email << ":\n";         \
    if(imagenes.tamlog() == 0)std::cout << "    nada encontrado\n";  \
    for (int i = 0; i < imagenes.tamlog(); ++i) {\
        std::cout <<"   "<< *imagenes[i];\
    }\

#define mostrarUsuarioEtiq(etiqueta) \
    usuarios = libro.buscarUsuarioEtiq(etiqueta); \
    std::cout << "\n" << etiqueta << ":\n";\
    for (int i = 0; i < usuarios.tamlog(); ++i) {\
    std::cout <<"   "<< usuarios[i]->getEmail() << "\n";\
    }\

int main()
{
    /************************************************************************************************
     * Probar la estructura, en una función independiente, instanciándola a AVL<unsigned int> con
     * un millón de enteros aleatorios en el rango [0, 1.000.000] y mostrar la altura del árbol por
     * pantalla (puede que no todos se inserten si están repetidos).
     * **********************************************************************************************/
    AVL<unsigned int> randomTree;
    srand(time(NULL));
    for (int i = 0; i <= 1000000; ++i) {
        unsigned int random = rand() % 1000001;
        randomTree.inserta(random);
    }
    std::cout << "Altura del arbol aleatorio: " << randomTree.altura() << '\n';
    /***********************************************************************************************
     * Instanciar la clase ImageBook según el diseño UML añadiendo los datos de los tres ficheros
     * anteriormente y siguiendo el procedimiento anteriormente descrito.
     * *********************************************************************************************/
    ImageBook libro("../etiquetas.txt","../usuarios.txt","../imagenes_v1.csv");
    /***********************************************************************************************************
     * Buscar y mostrar la información de las imágenes de estos usuarios (si es que existen): eliza39@yahoo.com,
     * betty95@hotmail.com, betty95@hotmail.com, victor6@gmail.com y manolete@gmail.com.
     * *********************************************************************************************************/
    {
        Usuario* usuario;
        VDinamico<Imagen *> imagenes;
        mostrarInfoImagenUsuario("eliza39@yahoo.com");
        mostrarInfoImagenUsuario("betty95@hotmail.com");
        mostrarInfoImagenUsuario("victor6@gmail.com");
        mostrarInfoImagenUsuario("manolete@gmail.com");
    }
    /*********************************************************************************************
     * Devolver y mostrar por pantalla todos aquellos usuarios que hayan publicado alguna imagen
     * con la etiqueta “playa” y posteriormente los que hayan publicado con la etiqueta “comida”.
     * *******************************************************************************************/
    {
        VDinamico<Usuario *> usuarios;
        mostrarUsuarioEtiq("playa")
        mostrarUsuarioEtiq("comida")
    }
    /*************************************************************************************
     * Devolver el/los usuarios más activos en la red porque hayan publicado más imágenes.
     * ***********************************************************************************/
    {
        VDinamico<Usuario *> activos = libro.getMasActivos();
        std::cout << "\nMas activo/s: \n";
        for (int i = 0; i < activos.tamlog(); ++i) {
            std::cout << "  " <<activos[i]->getEmail() << '\n';
        }
    }
    /*********************************************************************************
     * Medir el tiempo total de ejecución de 1000 operaciones de búsqueda de valores
     * aleatorios en el AVL<unsigned int> del segundo apartado.
     * *******************************************************************************/
    Timer clock;
    clock.start();
    for (int i = 0; i <= 1000; ++i) {
        unsigned int random = rand() % 1000001;
        randomTree.buscaRec(random);
    }
    clock.stop();
    std::cout <<"\ntiempo de las 1000 busquedas: "<< clock.getElapsedTimeInMilliSec();
    /***********************************************************************************
     * Recorrer en Inorden dicho árbol e introducir en un vector dinámico VDinamico<T>
     * los elementos que están en el rango [1000, 10.000].
     * *********************************************************************************/
    VDinamico<unsigned int*> inorden = randomTree.recorreInorden();
    VDinamico<unsigned int> rango;
    for (int i = 0; i < inorden.tamlog(); ++i) {
        if(*inorden[i]>=1000 && *inorden[i]<=10000)rango.insertar(*inorden[i]);
    }
    std::cout << "\n\ntamanno vector de rango[1000,10000]: " << rango.tamlog();
    std::cout << "\n\n200 primeros elementos:";
    for (int i = 0; i < 200; ++i) {
        std::cout << "\n    " << rango[i];
    }
    return 0;
}