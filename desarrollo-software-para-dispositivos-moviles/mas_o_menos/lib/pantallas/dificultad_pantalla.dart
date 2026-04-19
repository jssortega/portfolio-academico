import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:mas_o_menos/modelo/modelo.dart';

class DificultadPantalla extends StatelessWidget {
  const DificultadPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<Juego>(
        builder: (context,manager,child){
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Text(
                  'Selecciona la dificultad:',
                  style: TextStyle(fontSize: 25),
                ),
                const SizedBox(
                  height: 20.0,
                ),
                DropdownButton<Dificultad>(
                  value: manager.dificultad,
                  items: Dificultad.values.map((Dificultad dificultad) {
                    return DropdownMenuItem<Dificultad>(
                      value: dificultad,
                      child: Text(dificultad.name),
                    );
                  }).toList(),
                  onChanged: (nuevaDificultad) {
                    manager.dificultad = nuevaDificultad;
                    manager.empiezaJuego();
                  },
                ),
                const SizedBox(height: 20,),
                Text(
                  'Rango: 0-${manager.dificultad.rango}',
                  style: const TextStyle(fontSize: 20),
                ),
                const SizedBox(height: 30,),
                const Text(
                  '¿Quieres un reto?',
                  style: TextStyle(fontSize: 25),
                ),
                const Text(
                  'Solo con un intento',
                  style: TextStyle(fontSize: 20),
                ),
                const SizedBox(height: 10,),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(textStyle: const TextStyle(fontSize: 20)),
                  onPressed: () {
                    manager.dificultad = Dificultad.Challenge;
                    manager.empiezaJuego();
                  },
                  child: const Text(
                    'Challenge [1-10]',
                  ),
                ),
              ],
            ),
          );
        }
    );


  }
}
