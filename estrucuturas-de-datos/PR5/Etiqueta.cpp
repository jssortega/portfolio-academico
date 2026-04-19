//
// Created by gabis on 26/11/2022.
//

#include "Etiqueta.h"
#include "Imagen.h"

int Etiqueta::getTotalLikes() {
    int likes = 0;
    for (auto images: _etiImages) {
        likes += images->getLikes();
    }
    return likes;
}
