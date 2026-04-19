import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:mas_o_menos/modelo/modelo.dart';
import 'componentes.dart';

class Teclado extends StatefulWidget {
  const Teclado({super.key});


  @override
  State<Teclado> createState() => _TecladoState();
}

class _TecladoState extends State<Teclado> {
  int valor = 0;
  final valoresAnteriores = Pila<int>();

  void actualizaValor(int tecla){
    setState(() {
      valoresAnteriores.push(valor);
      valor = valor * 10 + tecla;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: MediaQuery.of(context).size.width,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Text(
                valor.toString(),
                style: TextStyle(fontSize: 30),
              ),
            ],
          ),
          SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: Column(
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("7"),
                              onPressed: (){actualizaValor(7);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("8"),
                              onPressed: (){actualizaValor(8);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("9"),
                              onPressed: (){actualizaValor(9);}
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("4"),
                              onPressed: (){actualizaValor(4);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("5"),
                              onPressed: (){actualizaValor(5);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("6"),
                              onPressed: (){actualizaValor(6);}
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("1"),
                              onPressed: (){actualizaValor(1);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("2"),
                              onPressed: (){actualizaValor(2);}
                          ),
                        ),
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("3"),
                              onPressed: (){actualizaValor(3);}
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: ElevatedButton(
                              child: const Text("0"),
                              onPressed: (){actualizaValor(0);}
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              Expanded(
                flex: 1,
                child: Column(
                  children: <Widget>[
                    Container(
                      height: 48,
                      child: ElevatedButton(
                          child: const Icon(Icons.arrow_back),
                          onPressed: (){
                            setState(() {
                              valor = valoresAnteriores.pop();
                            });
                          }
                      ),
                    ),
                    SizedBox(height: 5),
                    Container(
                      height: 139,
                      child: ElevatedButton(
                          child: const Icon(Icons.subdirectory_arrow_left),
                          onPressed: (){
                            final manager = Provider.of<Juego>(context, listen: false);
                            manager.valor = valor;
                            manager.calculaPistaNormal();
                            manager.numeroIntentos += 1;
                            manager.maxIntentos -= 1;
                            if(manager.maxIntentos == 0 && !manager.finalJuego){
                              partidaPerdida(context);
                            }
                            if(manager.finalJuego){
                              partidaGanada(context);
                            }
                            valor = 0;
                            valoresAnteriores.clear();
                          }
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );

  }

  void partidaGanada(BuildContext context) {
    final manager = Provider.of<Juego>(context, listen: false);
    manager.calculaPuntuacion();
    showDialog(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text(
              '¡Has acertado!',
              textAlign: TextAlign.center,
            ),
            content: Text(
              'Puntuación: ${manager.puntuacion}\n¿Quieres jugar otra vez?',
              textAlign: TextAlign.center,
            ),
            actions: <Widget>[
              TextButton(
                  child: const Text('Si'),
                  onPressed: () {
                    manager.valor = 0;
                    Navigator.of(context).pop();
                    manager.empiezaJuego();

                  }
              ),
              TextButton(
                child: const Text('No'),
                onPressed: () {
                  EstadoJuego.instancia.estado = false;
                  Navigator.of(context).pop();
                  dispose();
                },
              ),
            ],
          );
        }
    );
  }

  void partidaPerdida(BuildContext context) {
    final manager = Provider.of<Juego>(context, listen: false);
    manager.calculaPuntuacion();
    showDialog(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text(
              'Game over',
              textAlign: TextAlign.center,
            ),
            content: Text(
              'Puntuación: 0\n El numero era: ${manager.numeroAdivinar}\n ¿Quieres jugar otra vez?',
              textAlign: TextAlign.center,
            ),
            actions: <Widget>[
              TextButton(
                  child: const Text('Si'),
                  onPressed: () {
                    manager.valor = 0;
                    Navigator.of(context).pop();
                    manager.empiezaJuego();

                  }
              ),
              TextButton(
                child: const Text('No'),
                onPressed: () {
                  EstadoJuego.instancia.estado = false;
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