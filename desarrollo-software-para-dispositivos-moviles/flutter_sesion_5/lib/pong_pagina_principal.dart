import 'package:flutter/material.dart';
import 'package:flutter_sesion_5/rejilla_juego.dart';

class PongPaginaPrincipal extends StatefulWidget {
  const PongPaginaPrincipal({Key? key, required this.titulo}) : super(key: key);

  final String titulo;

  @override
  _PongPaginaPrincipalState createState() => _PongPaginaPrincipalState();
}


class _PongPaginaPrincipalState extends State<PongPaginaPrincipal> {
  bool estoyJugando = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.titulo,
          style: TextStyle(color: Theme.of(context).colorScheme.onPrimary,),
        ),
        backgroundColor: Theme.of(context).colorScheme.primary,
      ),
// 1
        body: SafeArea(
          child: estoyJugando ? RejillaJuego() : Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                Text('Pong: Presiona jugar para comenzar'),
                const SizedBox(
                  height: 32.0,
                ),
                ElevatedButton(
                  child: const Text(
                    'Jugar',
                  ),

                  onPressed: () {
                      setState(() {
                        estoyJugando = true;
                      });
                  },
                ),
              ],
            ),
          ),
        ),
    );
  }
}
