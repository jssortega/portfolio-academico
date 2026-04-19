#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: comprueba que se hayan pasado entre 2 o 4 parámetros

if [ ${#} -gt 4 ] || [ ${#} -lt 2 ] 
then
	echo "Error, tienes que pasar entre 2 o 4 parámetros, has pasado ${#}"
else
	echo ${*}
fi
