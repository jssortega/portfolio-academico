#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción:eciba como argumento un número, el UID de un usuario y que comprueba si existe en el sistema un usuario con ese UID. Si existe debe comprobar además si ese usuario tiene el mismo UID y GID.

if [ ${#} -ne 1 ]
then
	echo "Error, debe pasar unicamente un argumento"
else
	while read linea
	do
		uid=$(echo ${linea} | cut -d: -f3)
		guid=$(echo ${linea} | cut -d: -f4)
		
		if [ ${uid} -eq ${1} ]
		then
			if [ ${guid} -eq ${uid} ]
			then
				echo "El usuario con UID ${1} existe y tiene el mismo GUID"
				exit
			else
				echo "El usuario con UID ${1} existe y no tiene el mismo GUID"
				exit
			fi
		fi
		 
	done < /etc/passwd 
	
	echo "El usuario con UID ${1} no existe"
fi
