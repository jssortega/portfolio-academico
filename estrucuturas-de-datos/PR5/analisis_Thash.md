# Análisis de tablas de dispersión

* *Gabriel Soria Sánchez*
* *Jesús Ortega Castillo*

## Tamaño de tabla: 14713
| función         | máximo de colisiones | factor de carga | promedio de colisiones | Nº de veces que <br/>supera las 10 colisiones |
|-----------------|:--------------------:|:---------------:|:----------------------:|:---------------------------------------------:|
| (x+i^2)%t       |          20          |      0.68       |         0.7503         |                      28                       |
| (x+i*x%15391)%t |          17          |      0.68       |         0.6553         |                      12                       |
| (x+i*x%14713)%t |          15          |      0.68       |         0.7380         |                      17                       |
## Tamaño de tabla: 15391
| función         | máximo de colisiones | factor de carga | promedio de colisiones | Nº de veces que <br/>supera las 10 colisiones |
|-----------------|:--------------------:|:---------------:|:----------------------:|:---------------------------------------------:|
| (x+i^2)%t       |          15          |      0.65       |         0.7066         |                      19                       |
| (x+i*x%15391)%t |          16          |      0.65       |         0.6708         |                      14                       |
| (x+i*x%14713)%t |          17          |      0.65       |         0.6275         |                      11                       |

## Justificación de la configuración elegida
Hemos optado por la segunda de dispensión doble, dado que el promedio es menor y nos dará una busqueda más veloz. 