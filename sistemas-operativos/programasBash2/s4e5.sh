#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: Escribe un shell script que analice el archivo /etc/group y que diga si una serie de GIDs que se pasan como argumentos corresponden a grupos válidos del sistema. Al final debe escribir por pantalla cuántos de los GIDs pasados corresponden a grupos válidos y cuántos no.


if [ ${#} -eq 0 ]
then
	echo "Debe pasar al menos un elemento"
else
	while read linea
	do
		i=1
		guid=$(echo ${linea} | cut -d: -f3)
		
		while [ ${i} -le ${#} ]
		do
			
			if [ "${guid}" = "${!i}" ]
			then
				validos=${validos}" ${!i}"
				
			fi
		i=$((${i}+1)) 
		done 
		
	done < /etc/group
	
	echo "Los validos son ${validos}"
	
fi
