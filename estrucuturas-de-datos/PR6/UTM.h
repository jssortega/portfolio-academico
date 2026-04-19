/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   UTM.h
 * Author: Lorena
 *
 * Created on 14 de octubre de 2021, 11:25
 */

#ifndef UTM_H
#define UTM_H

class UTM {
public:
    UTM();
    UTM(float latitud, float longitud);
    UTM(const UTM& orig);
    virtual ~UTM();
    float GetLongitud() const;
    float GetLatitud() const;
private:
    float latitud;
    float longitud;
};

#endif /* UTM_H */

