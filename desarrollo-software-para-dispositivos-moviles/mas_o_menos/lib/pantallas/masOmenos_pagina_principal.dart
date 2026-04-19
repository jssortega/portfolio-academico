import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:mas_o_menos/modelo/modelo.dart';
import 'pantallas.dart';


class MasOMenosPaginaPrincipal extends StatefulWidget {
  const MasOMenosPaginaPrincipal({super.key, required this.titulo});
  final String titulo;

  @override
  State<MasOMenosPaginaPrincipal> createState() => _MasOMenosPaginaPrincipalState();
}

enum Categoria{
  dificultad(DificultadPantalla(),'Niveles', Icons.settings),
  juego(  JuegoPantalla(),'Juego', Icons.videogame_asset);

  const Categoria(this.pantalla,this.mensaje,this.icono);
  final Widget pantalla;
  final String mensaje;
  final IconData icono;


}

class _MasOMenosPaginaPrincipalState extends State<MasOMenosPaginaPrincipal> {
  int _categoriaActiva=0;

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
        body: construirPantallaJuego()

    );
  }

  Widget construirPantallaJuego(){
    return Consumer<Juego>(
        builder: (context,manager,child){
          return Consumer<EstadoJuego>(
              builder: (context,manager1,child) {
                return EstadoJuego.jugando ? Scaffold(
                  body:SafeArea(
                      child: Categoria.values[_categoriaActiva].pantalla
                  ),
                  bottomNavigationBar: BottomNavigationBar(
                    currentIndex: _categoriaActiva,
                    onTap: _alPulsar,
                    items: Categoria.values.map((categoria) {
                      return BottomNavigationBarItem(
                        icon: Icon(categoria.icono),
                        label: categoria.mensaje,
                      );
                    }).toList(),
                  ),
                ) : Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: <Widget>[
                      const Text(
                        'masOmenos:',
                        style: TextStyle(fontSize: 20),
                      ),
                      const SizedBox(height: 10,),
                      const Text(
                        'Adivina el número oculto,',
                        style: TextStyle(fontSize: 20),
                      ),
                      const Text(
                        'ten en cuenta el numero de intentos.',
                        style: TextStyle(fontSize: 20),
                      ),
                      const SizedBox(height: 25,),
                      const Text(
                        'Presiona jugar para comenzar',
                        style: TextStyle(fontSize: 20),
                      ),
                      const SizedBox(
                        height: 32.0,
                      ),
                      ElevatedButton(
                        child: const Text(
                          'Jugar',
                          style: TextStyle(fontSize: 20),
                        ),
                        onPressed: () {
                          manager.empiezaJuego();
                          EstadoJuego.instancia.estado = true;
                        },
                      ),
                    ],
                  ),
                );
              }
          );
        }
    );
  }


  void _alPulsar(int indice){
    setState(() => _categoriaActiva = indice);
  }

}
