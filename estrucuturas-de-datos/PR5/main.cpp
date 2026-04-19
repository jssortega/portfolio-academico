#include <iostream>
#include "ImageBook.h"
#include <sstream>
#include <ctime>

int main()
{
    /***********************************************************************************************
     * Instanciar la clase ImageBook según el diseño UML añadiendo los datos de los tres ficheros  *
     * anteriormente y siguiendo el procedimiento anteriormente descrito.                          *
     * *********************************************************************************************/
    ImageBook libro("../etiquetas.txt","../usuarios.txt","../imagenes_v1.csv");
    /***********************************************************************************************
     * Mostrar el factor de carga de la tabla junto al tamaño de la misma.                         *
     * *********************************************************************************************/
    std::cout<< "Tamanno de la tabla: " << libro.tamTabla() << "\nFactor de carga: " << libro.factorCarga();
    /***********************************************************************************************
     * El usuario kenny_ohara73@yahoo.com quiere darle like a la última imagen que ha subido el    *
     * usuario magdalen_upton99@gmail.com. Encontrar la imagen, mostrar sus datos y darle like.    *
     * Volver a mostrar los datos de la imagen.                                                    *
     * *********************************************************************************************/
    Imagen* imagen = libro.buscaUsuario("magdalen_upton99@gmail.com")->getImagenMasReciente();
    std::cout << "\n\n" << *imagen;
    libro.buscaUsuario("kenny_ohara73@yahoo.com")->meGustaImagen(libro.buscaUsuario("magdalen_upton99@gmail.com")->getImagenMasReciente());
    std::cout << *imagen;
    /***********************************************************************************************
     * El usuario beau1@hotmail.com quiere darle like a la imagen con id 32477162. Localizarla y   *
     * darle like.                                                                                 *
     * *********************************************************************************************/
    libro.buscaUsuario("beau1@hotmail.com")->meGustaImagen(libro.buscaImagen("32477162"));
    /***********************************************************************************************
     *  Darle like a todas las imágenes con la etiqueta “gato”                                     *
     * *********************************************************************************************/
    std::vector<Imagen*> gatoImgs = libro.buscarImagEtiq("gato");
    for (auto gatoImg : gatoImgs) {
        gatoImg->nuevoLike();
    }
    /***********************************************************************************************
     * Se quiere saber qué etiquetas son más influyentes. Para ello, obtener el top 5 de etiquetas
     * con más likes.
     * *********************************************************************************************/
    std::vector<Etiqueta*> top5 = libro.top5Etiq();
    std::cout << "\nTop 5 Etiquetas con mas likes: ";
    for(int i = 0;i < 5;++i){
        std::cout << "\n     "<< i+1 << ". " << top5[i]->getNombre();
    }
    /***********************************************************************************************
     * Se quiere saber qué usuarios son más populares. Para ello, mostrar el top 3 de usuarios
     * más populares.
     * *********************************************************************************************/
    std::vector<Usuario*> top3 = libro.top3User();
    std::cout << "\n\nTop 3 usuarios mas populares: ";
    for(int i = 0;i < 3;++i){
        std::cout << "\n     "<< i+1 << ". " << top3[i]->getEmail();
    }
    /***********************************************************************************************
     *  Obtener el número de likes de la etiqueta "pantalla"
     * *********************************************************************************************/
    std::cout << "\n\nLikes de la etiqueta 'pantalla': "<< libro.buscaEtiqueta("pantalla")->getTotalLikes();
    /***********************************************************************************************
     *  Buscar y eliminar la imagen con id 58540348.
     * *********************************************************************************************/
     Imagen* buscadaImg = libro.buscaImagen("58540348");
    libro.borrarImg("58540348");
    std::cout << "\nLa imagen '58540348' es borrada";
    /***********************************************************************************************
     *  Obtener el número de likes de la etiqueta "pantalla"
     * *********************************************************************************************/
    std::cout << "\nLikes de la etiqueta 'pantalla': "<< libro.buscaEtiqueta("pantalla")->getTotalLikes();
    /***********************************************************************************************
     *  Comprobar que no está la imagen 58540348 tras el borrado mediante una búsqueda e insertar
     *  dicha imagen de nuevo.
     * *********************************************************************************************/
    buscadaImg = libro.buscaImagen("58540348");
    buscadaImg ? std::cout<<"\nExiste" : std::cout<<"\nNo existe";
    Imagen nuevo("58540348","Imagen36971.raw",602030,18,2,2020,348);
    libro.nuevaImagen(nuevo,"abigail.waelchi@yahoo.com");
    Imagen* nuevoPtr = libro.buscaImagen("58540348");
    nuevoPtr->anadirEtiqueta(libro.buscaEtiqueta("permiso"));
    nuevoPtr->anadirEtiqueta(libro.buscaEtiqueta("diferencia"));
    nuevoPtr->anadirEtiqueta(libro.buscaEtiqueta("aburrimiento"));
    nuevoPtr->anadirEtiqueta(libro.buscaEtiqueta("pantalla"));
    nuevoPtr->anadirEtiqueta(libro.buscaEtiqueta("adulta"));
    /***********************************************************************************************
     *  Mostrar el número de colisiones máximo que se han producido al volver a insertar la imagen.*
     * *********************************************************************************************/
    std::cout << "\n\nMaximo de colisiones: " << libro.maxColisiones();
    /***********************************************************************************************
     *  Probar el comportamiento del método añadiendo 5 imágenes nuevas a ImageBook y
     *  mostrando después el estado de la tabla
     * *********************************************************************************************/
    srand(time(NULL));
    for (int i = 0; i < 6; ++i) {
        std::stringstream id;
        Imagen image;
        id << 10000000000+rand()%10000000000;
        image =Imagen(id.str(), "prueba", 3772, Fecha(),1,std::deque<Etiqueta*>());
        libro.nuevaImagen(image,"admin@admin.com");
    }
    std::cout << "\n\n" << libro.mostrarEstadoTablaImagenes();
    return 0;
}