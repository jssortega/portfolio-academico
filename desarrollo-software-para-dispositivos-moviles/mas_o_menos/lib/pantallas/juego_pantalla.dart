import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:mas_o_menos/modelo/modelo.dart';
import 'package:mas_o_menos/componentes/componentes.dart';

class JuegoPantalla extends StatelessWidget {
  const JuegoPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<Juego>(
        builder: (context,manager,child){
          return Column(
            children: <Widget>[
              const SizedBox(height: 20,),

              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  ElevatedButton(
                    child: const Icon(Icons.emoji_objects_outlined),
                    onPressed: () {
                      manager.calculaPistaEspecial();
                      showDialog(
                          context: context,
                          builder: (BuildContext context) {
                            return AlertDialog(
                              title: const Text(
                                'Pista:',
                                textAlign: TextAlign.center,
                              ),
                              content: Text(
                                manager.mensajePista,
                                textAlign: TextAlign.center,
                                style: const TextStyle(fontSize: 20),
                              ),
                              actions: <Widget>[
                                TextButton(
                                    child: const Text('Aceptar'),
                                    onPressed: () {
                                      Navigator.of(context).pop();
                                    }
                                ),
                              ],
                            );
                          }
                      );
                    },
                  ),
                  const SizedBox(width: 15,)
                ],
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Intentos restantes:${manager.maxIntentos.toString()}",
                    style: const TextStyle(fontSize: 20),
                  ),
                ],
              ),
              Expanded(
                child: Align(
                  alignment: Alignment.center,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            "Número introducido:",
                            style: TextStyle(fontSize: 25),
                          ),
                        ],
                      ),
                      const SizedBox(height: 15,),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            manager.valor.toString(),
                            style: const TextStyle(fontSize: 35),
                          ),
                          manager.pista,
                        ],
                      ),

                    ],
                  ),
                ),
              ),

              Teclado(),

              const SizedBox(height: 20,)
            ],
          );
        }
    );
  }
}
