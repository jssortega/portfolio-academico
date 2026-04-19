import 'package:flutter/material.dart';
import 'package:flutter_sesion_5/raqueta.dart';
import 'package:flutter_sesion_5/pelota.dart';

// 12
enum Direccion {
  arriba, abajo, izquierda, derecha,
}
class RejillaJuego extends StatefulWidget {
  const RejillaJuego({Key? key}) : super(key: key);
  @override
  State<RejillaJuego> createState() => _RejillaJuegoState();
}
// 10
class _RejillaJuegoState extends State<RejillaJuego>
    with SingleTickerProviderStateMixin {
// 3
  double anchoRejilla = 0.0;
  double altoRejilla = 0.0;
  double anchoRaqueta = 0.0;
  double altoRaqueta = 0.0;
// 5
  late double diametroPelota;
// 7
  late AnimationController controladorAnimacion;
  late double xPelota;
  late double yPelota;
// 13
  late Direccion direccionVertical;
  late Direccion direccionHorizontal;
// 15
  late double incremento;
// 18
  late double xRaqueta;
// 21
  late double mitadPelota;
// 25
  late int puntuacion;
  late int dificultad;
  @override
  void initState() {
    diametroPelota = 40.0;
// 9
    xPelota = 0.0;
    yPelota = 0.0;
// 14
    direccionVertical = Direccion.abajo;
    direccionHorizontal = Direccion.derecha;
// 16
    incremento = 5.0;
// 19
    xRaqueta = 0.0;
// 22
    mitadPelota = diametroPelota/2.0;
// 26
    puntuacion = 0;
    dificultad = 5;
// 17
    controladorAnimacion = AnimationController(
      duration: const Duration(minutes: 10000),
      vsync: this,
    );
// 11
    controladorAnimacion.addListener(() {
      setState(() {
        (direccionHorizontal == Direccion.derecha) ? xPelota += incremento :
        xPelota -= incremento;
        (direccionVertical == Direccion.abajo) ? yPelota += incremento :
        yPelota -= incremento;
      });
      comprobarBordes();
    });
    controladorAnimacion.forward();
    super.initState();
  }

  @override
  void dispose() {
    controladorAnimacion.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
// 2
          anchoRejilla = constraints.maxWidth;
          altoRejilla = constraints.maxHeight;
          anchoRaqueta = anchoRejilla / 4.0;
          altoRaqueta = altoRejilla / 20.0;
          return Stack(
            children: <Widget>[
              Positioned(
// 8
                top: yPelota,
                left: xPelota,
// 6
                child: Pelota(diametro: diametroPelota),
              ),
// 20
              Positioned(
                bottom: 0,
                left: xRaqueta,
                child: GestureDetector(
                    onHorizontalDragUpdate: (DragUpdateDetails detalleDeslizar) {
                      moverRaqueta(detalleDeslizar);
                    },
                    child: Raqueta(anchura: anchoRaqueta, altura: altoRaqueta,)
                ),
              ),
// 27
              Positioned(
                top: 12,
                right: 12,
                child: Text(
                  'Puntuación: $puntuacion',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                  ),
                ),
              ),
            ],
          );
        }
    );
  }

  void comprobarBordes() {
// 24
    if (anchoRejilla == 0.0 || altoRejilla == 0.0) { return; }
    double bordeDerecho = anchoRejilla - diametroPelota;
    double bordeInferior = altoRejilla - diametroPelota - altoRaqueta;
    if (xPelota <= 0 && direccionHorizontal == Direccion.izquierda) {
      direccionHorizontal = Direccion.derecha;
    } else if (xPelota >= bordeDerecho && direccionHorizontal == Direccion.derecha)
    {
      direccionHorizontal = Direccion.izquierda;
    }
    if (yPelota <= 0 && direccionVertical == Direccion.arriba) {
      direccionVertical = Direccion.abajo;
    } else if (yPelota >= bordeInferior && direccionVertical == Direccion.abajo) {
// 23
      if (xPelota >= (xRaqueta - mitadPelota) &&
          xPelota <= (xRaqueta + anchoRaqueta - mitadPelota)) {
        direccionVertical = Direccion.arriba;
// 28
        setState(() {
          puntuacion++;
          if(puntuacion > dificultad){
            incremento++;
            dificultad += 5;
          }
        });
      } else {
        controladorAnimacion.stop();
// 29
        preguntarRepetirPartida(context);
      }
    }
  }

  void moverRaqueta(DragUpdateDetails detalleDeslizar) {
    setState(() {
      xRaqueta += detalleDeslizar.delta.dx;
      if (xRaqueta <= 0) {
        xRaqueta = 0.0;
      } else if (xRaqueta >= anchoRejilla - anchoRaqueta) {
        xRaqueta = anchoRejilla - anchoRaqueta;
      }
    });
  }

  void preguntarRepetirPartida(BuildContext context) {
    showDialog(
        context: context,
        builder: (BuildContext context) {
      return AlertDialog(
          title: const Text(
          'Game Over',
          textAlign: TextAlign.center,
      ),content: Text(
        'Puntuación: $puntuacion\n¿Quieres jugar otra vez?',
        textAlign: TextAlign.center,
      ),
        actions: <Widget>[
          TextButton(
            child: const Text('Si'),
            onPressed: () {
              setState(() {
                xPelota = 0.0;
                yPelota = 0.0;
                puntuacion = 0;
              });
              Navigator.of(context).pop();
              controladorAnimacion?.repeat();
            },
          ),
          TextButton(
            child: const Text('No'),
            onPressed: () {
              Navigator.of(context).pop();
              dispose();
            },
          ),
        ],
      );
        }
    );
  }
}