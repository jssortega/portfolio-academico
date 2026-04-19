#!/bin/bash

#Autor:Jesús Ortega Castillo
#Descripcion:eciba exactamente dos argumentos que sean cadenas de caracteres y diga si la primera está ordenada alfabéticamente con respecto a la segunda o no.

if [ ${#} -ne 2 ]
then 
	echo "Error tiene que pasar dos argumentos"
elif [[ ${1} < ${2} ]]
then
	echo " La primera está ordenada alfabéticamente respecto la segunda."
else
	echo " La primera no está ordenada alfabéticamente respecto la segunda."
fi
