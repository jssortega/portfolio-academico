#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: Escribe un shell script que saque una lista por pantalla de aquellos usuarios del sistema que están bloqueados. Recuerda que un usuario bloqueado tiene en el archivo /etc/shadow un signo ! en lugar de una contraseña cifrada. Recuerda que para acceder a /etc/shadow hay que tener permisos de root.

if [ $(whoami) = "root" ]
then

	echo "Usuarios bloqueados:"

	while read linea
	do
		estado=$(echo ${linea} | cut -d: -f2)
		usuario=$(echo ${linea} | cut -d: -f1)
	
		if [ "${estado}" = "!" ]
		then
			echo "${usuario}"
			echo "";
		fi
	
	done < /etc/shadow
else
	echo "No eres root"
fi
