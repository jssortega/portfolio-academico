#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: El archivo /etc/group tiene una línea por cada grupo que haya creado en el sistema. Investiga el formato de este archivo y escribe un script que escriba por pantalla cuales son los grupos que tienen usuarios asignados. Al final deberá escribir el número de grupos que tienen usuarios asignados.

echo "Los grupos con usuarios asignados son: "
contador=0
while read linea
do
	usuarios=$(echo ${linea} | cut -d: -f4)
	if [ -n "${usuarios}" ]
	then
		echo "$(echo ${linea} | cut -d: -f1)"
		contador=$((${contador}+1))
	fi
done < /etc/group

echo "${contador} en total"
