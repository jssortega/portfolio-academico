#!/bin/bash

#Autor: Jesús Ortega Castillo

while read linea
do
	nombre=$(echo ${linea} | cut -d: -f1)
	
	if [ "${nombre}" = "Buffers" ]  || [ "${nombre}" = "PageTables" ]
	then
		kb=$(echo ${linea} | cut -d: -f2)
		kbnum=$(echo ${kb} | cut -d" " -f1)
		echo "Memoria de ${nombre}: $((${kbnum}/1024)) mb" 
	fi 
done < /proc/meminfo
