/****************************************************
 * @author Gabriel Soria Sánchez gss00016@red.ujaen.es
 * @author Jesús Ortega Castillo joc00023@red.ujaen.es
 ****************************************************/

#include <iostream>
#include "ImageBook.h"
#include <ctime>

int main()
{
    /***********************************************************************************************
     * Implementar la misma funcionalidad de la Práctica 5, exceptuando que ahora no               *
     * usamos una tabla hash en la relación ImageBook::images sino un std::map                     *
     * *********************************************************************************************/
    ImageBook libro("../etiquetas.txt","../usuarios.txt","../imagenes_v2_mod.csv");
    /***********************************************************************************************
     * Mostrar los identificadores de las imágenes que se encuentran en el rango                   *
     * (rxmin=34.04, rymin=-81.06) y (rxmax=55.04, rymax=-61.06) y que comparten las               *
     * etiquetas de la imagen más reciente del usuario “kenny_ohara73@yahoo.com”.                  *
     * *********************************************************************************************/
    std::cout << "Imagenes en rango y con etiqueta de kenny:\n" ;
    Imagen* kennyImage = libro.buscaUsuario("kenny_ohara73@yahoo.com")->getImagenMasReciente();
    for(auto & image : libro.buscarImagLugar(34.04,-81.06,55.04,-61.06)){
        for(auto & etiqueta : kennyImage->getEtiquetada()){
            if(image->contieneEtiqueta(etiqueta->getNombre())){
                std::cout << "\n           " << image->getId();
                break;
            }
        }
    }
    /***********************************************************************************************
     * Mostrar el email de todos los usuarios que han tomado una foto en el rango                  *
     * (rxmin=36.388698, rymin=-121.72439) y (rxmax=39.388698, rymax=-89.72439)                    *
     * *********************************************************************************************/
    std::cout << "\n\nUsuarios en rango:\n" ;
    for(auto & user : libro.buscarUsuarLugar(36.388698,-121.72439,39.388698,-89.72439)){
        std::cout << "\n        " << user->getEmail();
    }
    /***********************************************************************************************
     * Mostrar el nombre de la etiqueta que más se repite en aquellas imágenes localizadas         *
     * en el rango (rxmin=30.0201, rymin=-98.2340) y (rxmax=-60.0039, rymax=-80.99).               *
     * *********************************************************************************************/
     std::cout << "\n\nEtiqueta mas repetida en rango: " <<libro.buscaEtiquetaRepetida(30.0201,-98.2340,60.0039,-80.99)->getNombre();
     /***********************************************************************************************
      * Buscar las imágenes del usuario “beau1@hotmail.com” que se encuentran localizadas           *
      * en el rango (rxmin=30.8304, rymin=-94.8684) y (rxmax=47.3304, rymax=-62.3684) y             *
      * obtener de ellas la imagen con más likes (en caso de empate coger una de ellas). A          *
      * continuación, dar like a aquellas imágenes que están localizadas dentro del rango de la     *
      * imagen con más likes (rxmin=longitudImagenMásLikes-0.1,                                     *
      * rymin=latitudImagenMásLikes-0.1) y (rxmax=longitudImagenMásLikes+0.1,                       *
      * rymax=latitudImagenMásLikes+0.1). Para comprobar que los likes se han asignado              *
      * correctamente, mostrar los likes de las imágenes antes y después del cambio.                *
      * *********************************************************************************************/
     Imagen* masLikes = nullptr;
     Usuario* beau = libro.buscaUsuario("beau1@hotmail.com");
    std::cout << "\n\nLike a imagenes en rango con etiqueta: ";
     for(auto & image : beau->imagenEnZona(30.8304,-94.8684,47.3304,-62.3684)){
         masLikes = !masLikes || masLikes->getLikes()<image->getLikes() ? image : masLikes;
     }
     for(auto & image : libro.buscarImagLugar(masLikes->getX()-0.1,masLikes->getY()-0.1,masLikes->getX()+0.1,masLikes->getY()+0.1)){
         std::cout << "\n\n     likes antes: " << image->getLikes();
         beau->meGustaImagen(image);
         std::cout << "\n     likes despues: " << image->getLikes();
     }
     /**************************************************************************************************
      * En los próximos días se va a inaugurar un nuevo centro comercial en la ciudad de Jaén
      * llamado JaénPlaza (longitud=30, latitud=-75). Este centro comercial ha organizado un sorteo
      * de una Playstation 5 para todos aquellos usuarios que hayan asistido el día de la inauguración.
      * Para certificar que una persona ha asistido al día de la inauguración, deberán de tomar una
      * foto en el centro comercial, subirla a nuestra red social y etiquetarla con la etiqueta
      * (#JaenPlazaPlay5). Los asistentes al evento serán todos los usuarios cuyo email comience por
      * la letra ‘e’.
      *
      * Una vez todos los asistentes hayan realizado el proceso de hacer la fotografía y subirla a la
      * plataforma con el hashtag mencionado, se procederá a hacer el sorteo. Para ello, se
      * comprobará que todas las imágenes etiquetadas se encuentran en el rango de la localización
      * del centro comercial y, de entre todos los que cumplan la condición, se escogerá un usuario al
      * azar mediante un random
      **************************************************************************************************/
    vector<Imagen*> sortea2;
     for(auto & image : libro.buscaEtiqueta("#JaenPlazaPlay5")->getImages()){
         if(image->getX() > 29 && image->getX() < 31 && image->getY() > -76 && image->getY() < -74)
             sortea2.push_back(image);
     }

     int a = rand()%(sortea2.size()-1);

     int t = sortea2.size();

     std::cout << "\n\nGana: " << libro.buscarUsuarioImg(sortea2[rand()%(sortea2.size()-1)])->getEmail();

     libro.crearImagenMapa();
    return 0;
}