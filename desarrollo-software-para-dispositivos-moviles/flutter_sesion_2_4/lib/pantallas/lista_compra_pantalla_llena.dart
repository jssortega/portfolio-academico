import 'package:flutter/material.dart';
import 'package:flutter_sesion_2_4/componentes/componentes.dart';
import 'package:flutter_sesion_2_4/modelo/modelo.dart';
import 'package:flutter_sesion_2_4/pantallas/pantallas.dart';



class ListaCompraPantallaLlena extends StatelessWidget {
  const ListaCompraPantallaLlena({Key? key, required this.listaCompra}) :
        super(key: key);
  final ListaCompra listaCompra;
  @override
  Widget build(BuildContext context) {
    final productos = listaCompra.productos;
    return Padding(
      padding: const EdgeInsets.all(10.0),
      child: ListView.separated(
        itemCount: productos.length,
        separatorBuilder: (context, index) {
          return const SizedBox(height: 8.0);
        },
        itemBuilder: (context, index) {
          final producto = productos[index];
          // 18
          return Dismissible(
            key: Key(producto.id),
            direction: DismissDirection.endToStart,
            background: Container(
              color: Colors.red,
              alignment: Alignment.centerRight,
              child: const Icon(
                  Icons.delete_forever,
                  color: Colors.white,
                  size: 35.0
              ),
            ),
            onDismissed: (direction) {
              listaCompra.borraProducto(index);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('${producto.nombre} borrado'),
                ),
              );
            },
            child: InkWell(
              key: Key(producto.id),
              child: LineaProducto(
                producto: producto,
                completar: (valor) {
                  if (valor != null) {
                    listaCompra.marcaCompletado(index, valor);
                  }
                },
              ),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) =>
                        ListaCompraAnadirProducto(
                          productoOriginal: producto,
                          editarProducto: (producto) {
                            listaCompra.actualizaProducto(producto, index);
                            Navigator.pop(context);
                          },
                          crearProducto: (producto) {},
                        ),
                  ),
                );
              },
            ),
          );
        }
        ),
    );
  }
}