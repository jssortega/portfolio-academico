#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripcion: recibe el nombre de un directorio, si este no existe lo crea  con los permisos drwx------

if [ ${#} -ne 1 ]
then
	echo "Error tiene que pasar exclusivamente un parámetro"
elif [ -d ${HOME}/${1} ]
then 
	echo "Asignando permisos al directorio..."
	chmod 700 ${HOME}/${1}
else
	echo "El directorio no existe"
	echo "Creando directorio..."
	mkdir ${HOME}/${1}
	chmod 700 ${HOME}/${1}
fi
