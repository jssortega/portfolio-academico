#!/bin/bash

#Autor: Jesús Ortega Castillo
#Descripción:Escribe un shell script que busque, en todos los directorios que cuelgan del directorio base del usuario que ejecuta el script, si hay algún archivo que tenga como nombre core y que borre todos los archivos core encontrados. Al final del script se debe imprimir el número de archivos core borrados. Recuerda que la orden find con la opción -name nombrearchivo permite buscar archivos en el disco. Para más información consulta la sintaxis de la orden find.

borrados=0

for i in $(find ${HOME} -name *core*)
do
	if [ ! -d ${i} ]
	then
		rm ${i}
		borrados=$((${borrados}+1))
	fi
done

echo "Se han borrado ${borrados} archivos"
