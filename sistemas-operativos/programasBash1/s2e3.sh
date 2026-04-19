#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: recibe un nombre de ususario y comprueba si existe el el archivo .profile
# en su directorio base, si no existe lo copia de /etc/skel y le asigna permisos

if [ ${#} -ne 1 ]
then
	echo "Error tiene que pasar exclusivamente un parámetro"
elif [ -e /home/${1}/.profile ]
then 
	echo "Existe el archivo .profile de ${1}"
else
	echo "No existe el archivo .profile"
	echo "Copiando el archivo..."
	cp /etc/skel/.profile /home/${1}/
	echo "Asignando permisos..."
	chmod 644 /home/${1}/.profile
fi
