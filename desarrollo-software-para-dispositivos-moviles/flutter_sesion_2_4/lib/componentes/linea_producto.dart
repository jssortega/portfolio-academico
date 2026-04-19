import 'package:flutter/material.dart';
import 'package:flutter_sesion_2_4/modelo/modelo.dart';

class LineaProducto extends StatelessWidget {
  final Producto producto;
  final TextDecoration textDecoration;
// 19
  final Function(bool?)? completar;
// 20
  LineaProducto({Key? key, required this.producto, required this.completar})
      : textDecoration = producto.completado
      ? TextDecoration.lineThrough
      : TextDecoration.none,
        super(key: key);
  @override
  Widget build(BuildContext context) {
    var titleLarge = Theme.of(context).textTheme.titleLarge;
    var decortitleLarge = titleLarge?.copyWith(decoration: textDecoration);
    return Container(
      height: 60.0,
      child: Row(
// - Número ⓵ en el diagrama
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Row(
// - Número ⓶ en el diagrama
            children: <Widget>[
              const SizedBox(
                width: 8,
              ), // - Número ⓹ en el diagrama
              Column(
// - Número ⓸ en el diagrama
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
// - Número ⓻ en el diagrama
                    producto.nombre,
                    style: decortitleLarge!,
                  ),
                  const SizedBox(height: 4.0),
                  construirImportancia(
                      context, producto), // - Número ⓺ en el diagrama
                ],
              ),
            ],
          ),
          Row(
// - Número ⓷ en el diagrama
            children: <Widget>[
              Text(
// - Número ⓼ en el diagrama
                producto.cantidad.toString(),
                style: titleLarge,
              ),
              Checkbox(
// - Número ⓽ en el diagrama
                value: producto.completado,
// 21
                onChanged: completar,
              ),
            ],
          ),
        ],
      ),
    );
  }
  Widget construirImportancia(BuildContext context, Producto producto) {
    var temaTexto = Theme.of(context).textTheme.bodyMedium;
    var temaTextoColoreado = temaTexto?.copyWith(
        color: producto.importancia == Importancia.alta
            ? Colors.red
            : temaTexto?.color);
    return Text(
      producto.importancia.name,
      style: temaTextoColoreado!,
    );
  }
}