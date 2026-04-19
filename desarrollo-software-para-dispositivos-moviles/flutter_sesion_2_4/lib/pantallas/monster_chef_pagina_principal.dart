import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_sesion_2_4/pantallas/pantallas.dart';
import 'package:provider/single_child_widget.dart';

class MonsterChefPaginaPrincipal extends StatefulWidget {
  final String titulo;
  const MonsterChefPaginaPrincipal({this.titulo = '', super.key});

  @override
  State<MonsterChefPaginaPrincipal> createState() => _MonsterChefPaginaPrincipalState();
}

enum Categoria{
  listaCompra(  ListaCompraPantalla(),'Lista compra', Icons.list),
  recetas(ListaRecetasPantalla(),'Recetas', Icons.grid_view_rounded);

  const Categoria(this.pantalla,this.mensaje,this.icono);
  final Widget pantalla;
  final String mensaje;
  final IconData icono;


}

class _MonsterChefPaginaPrincipalState extends State<MonsterChefPaginaPrincipal> {
  int _categoriaActiva=0;


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.titulo),
      ),
      body: SafeArea(
          // 2
          child: Categoria.values[_categoriaActiva].pantalla
      ),
      // 1
      bottomNavigationBar: BottomNavigationBar(
        // 3
        currentIndex: _categoriaActiva,
        onTap: _alPulsar,
        items: Categoria.values.map((categoria) {
          return BottomNavigationBarItem(
              icon: Icon(categoria.icono),
              label: categoria.mensaje,
          );
        }).toList(),
      ),
    );
  }

  void _alPulsar(int indice){
    setState(() => _categoriaActiva = indice);
  }
}
