#!/bin/bash
# Autor: Francisco de Asís Conde Rodríguez
# Descripción: Pruebas de uso de variables

var1=3
var2=${var1}hola
var1hola=ves
var3=$var1hola

echo El contenido de var1 es: ${var1}
echo El contenido de var2 es: ${var2}
echo El contenido de var3 es: ${var3}
