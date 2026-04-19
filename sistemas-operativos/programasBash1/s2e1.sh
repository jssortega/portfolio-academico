#!/bin/bash

# Autor: Francisco de Asís Conde Rodríguez
# Descripción: Comprueba si al script se le han pasado justamente dos argumentos.

if [ ${#} -ne 2 ]
then
	echo "Error, se han pasado ${#} argumento(s)"
fi
