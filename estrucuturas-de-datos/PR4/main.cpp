#include <iostream>
#include "ImageBook.h"

int main()
{
    /***********************************************************************************************
     * Instanciar la clase ImageBook según el diseño UML añadiendo los datos de los tres ficheros  *
     * anteriormente y siguiendo el procedimiento anteriormente descrito.                          *
     * *********************************************************************************************/
    ImageBook libro("../etiquetas.txt","../usuarios.txt","../imagenes_v1.csv");

   /*********************************************************************************************
    * El usuario noelia30@hotmail.com quiere incluir la etiqueta “playa” en una de sus imágenes *
    * cuyo id es 625722993.                                                                     *
    * *******************************************************************************************/
   Usuario* buscado = libro.buscaUsuario("noelia30@hotmail.com");
   buscado->anadirEtiquetaImagen("625722993", "playa");
   /*********************************************************************************************
    * El usuario kenny_ohara73@yahoo.com quiere modificar la última imagen que ha subido.
    * Encontrar dicha imagen y añadirle la etiqueta “viernes”.
    * *******************************************************************************************/
   buscado = libro.buscaUsuario("noelia30@hotmail.com");
   buscado->anadirEtiquetaImagen(buscado->getImagenMasReciente()->getId(), "viernes");
   /*********************************************************************************************
    * El usuario elton.botsford@yahoo.com quiere conocer a todos los usuarios con los que
    * comparte la etiqueta “arroz”. Mostrar el número de usuarios obtenido y su email.
    * *******************************************************************************************/
    vector<Usuario*> users = libro.buscarUsuarioEtiq("arroz");
    std::cout << "\nUsuarios con etiqueta 'arroz': \n\n";
    for (auto user : users) {
        std::cout << "  " << user->getEmail() << '\n';
    }
    std::cout << "\nnumero de usuarios con etiqueta 'arroz': "<< users.size() << "\n\n";
    /*********************************************************************************************
     * Buscar a los usuarios que publicaron una imagen el día 7/9/2021 y mostrar sus datos.
     * De entre todos los usuarios, mostrar quién ha publicado más imágenes.
     * *******************************************************************************************/
    users = libro.buscarUsuarioFechaImagen(Fecha(7,9,2021));
    std::cout << "Usuarios que publicaron el 7/9/2021: \n\n";
    for (auto user : users) {
        buscado = buscado->getNumImages()<user->getNumImages() ? user : buscado;
        std::cout << "  " << user->getEmail() << '\n';
    }
    std::cout << "\nUsuario con mas imagenes (Teniendo una imagen con la etiqueta arroz): " << buscado->getEmail() << '\n';
    /*********************************************************************************************
     * Comprobar si el usuario chesley.gerlach@hotmail.com es el más activo de la red social.
     * *******************************************************************************************/
    libro.buscaUsuario("chesley.gerlach@hotmail.com")->esMasActivo() ? std::cout << "\nEs el mas activo\n" : std::cout << "\nNo hace una mierda\n";
    /*********************************************************************************************
     * Busca el o los usuarios más antiguos de la red social (aquellos que fueron los primeros
     * en publicar una imagen) y mostrar sus datos.
     * *******************************************************************************************/
    auto buscados = libro.buscarUsuariosPremium();
    std::cout << "\nUsuarios Premium: \n\n";
    for(auto user : buscados){
        std::cout << "  " << user->getEmail() << '\n';
    }
    return 0;
}