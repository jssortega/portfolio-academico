/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   UTM.cpp
 * Author: Lorena
 * 
 * Created on 14 de octubre de 2021, 11:25
 */

#include "UTM.h"

UTM::UTM():latitud(0.0), longitud(0.0)
{
}

UTM::UTM(float latitud, float longitud):latitud(latitud), longitud(longitud)
{
}

UTM::UTM(const UTM& orig): latitud(orig.latitud), longitud(orig.longitud) 
{
}

UTM::~UTM() {
}

float UTM::GetLongitud() const {
    return longitud;
}

float UTM::GetLatitud() const {
    return latitud;
}

