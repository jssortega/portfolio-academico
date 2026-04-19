#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción: scribe un shell script que reciba como argumento el nombre de un nuevo shell script que se quiere escribir y simplifique todos esos pasos

if [ ${#} -ne 1 ]
then
	echo "Error, debe pasar un argumento" 
else
	type -a ${1}
	if [ ${?} -eq 1 ]
	then
		touch ${HOME}/bin/${1}
		cx ${HOME}/bin/${1}
	else
		echo "Error, ${1} es una orden interna del shell"
	fi
fi
