#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: enombre todos los archivos ejecutables del directorio ~/bin, de forma que le añada los caracteres 

if [ -d ${HOME}/bin ]
then
	for i in $( ls ${HOME}/bin/ )
	do
		if [ -x ${HOME}/bin/${i} ]
		then
			mv ${HOME}/bin/${i} ${HOME}/bin/${i}.sh
		fi
	done
else
	echo "Error, no existe el directorio bin"
fi
