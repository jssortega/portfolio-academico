import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';
import 'package:flutter_sesion_2_4/modelo/modelo.dart';
import 'package:uuid/uuid.dart';
import 'package:input_quantity/input_quantity.dart';

class ListaCompraAnadirProducto extends StatefulWidget {
  final Function(Producto) crearProducto;
  final Function(Producto) editarProducto;
  final Producto? productoOriginal;
  final bool actualizando;
  const ListaCompraAnadirProducto({
    Key? key,
    required this.crearProducto,
    required this.editarProducto,
    this.productoOriginal,
  }) : actualizando = (productoOriginal != null),
        super(key: key);
  @override
  _ListaCompraAnadirProductoState createState() =>
      _ListaCompraAnadirProductoState();
}

class _ListaCompraAnadirProductoState extends State<ListaCompraAnadirProducto> {
  final _controladorNombre = TextEditingController();
  String _nombre = '';
  bool _completado = false;
  Importancia _importancia = Importancia.baja;
  int _cantidad = 0;
  @override
  void initState() {
    super.initState();
    _controladorNombre.addListener(() {
      setState(() { _nombre = _controladorNombre.text; });
    });
    final productoOriginal = widget.productoOriginal;
    if (productoOriginal != null) {
      _controladorNombre.text = productoOriginal.nombre;
      _nombre = productoOriginal.nombre;
      _cantidad= productoOriginal.cantidad;
      _importancia = productoOriginal.importancia;
      _completado = productoOriginal.completado;
    }
  }


  @override
  void dispose() {
    _controladorNombre.dispose();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
            icon: const Icon(Icons.check),
            // 8
            onPressed: () {
              final producto = Producto(
                id: widget.productoOriginal?.id ?? const Uuid().v1(),
                nombre: _controladorNombre.text,
                importancia: _importancia,
                cantidad: _cantidad ,
              );
              if (widget.actualizando) {
                widget.editarProducto(producto);
              } else {
                widget.crearProducto(producto);
              }
            },
          ),
        ],
        elevation: 0.0,
        title: const Text( 'Añadir/editar', ),
      ),
      body: Container(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: <Widget>[
            construyeCampoNombre(),
            const SizedBox(height: 16,),
            construyeCampoImportancia(),
            // 16
            const SizedBox(
              height: 16,
            ),
            construyeCampoCantidad(),
          ],
        ),
      ),
    );
  }
  
  Widget construyeCampoNombre() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'Nombre del producto:',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        TextField(
          controller: _controladorNombre,
          decoration: const InputDecoration(
            border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(15))),
            hintText: 'P.e.: Pan, 1kg de sal, etc.',
          ),
        ),
      ],
    );
  }

  Widget construyeCampoImportancia() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
      Text(
      'Importancia',
      style: Theme.of(context).textTheme.titleSmall,
    ),
    Wrap(
    spacing: 10.0,
    children: Importancia.values.map((elemento) {
    return ChoiceChip(
    selected: _importancia == elemento,
    shape: StadiumBorder(),
    label: Text(
    elemento.name,
    ),
      onSelected: (selecion) {
      setState(() { _importancia = elemento; });
    },
    );
    }).toList(),
    )
      ],
    );
  }

  Widget construyeCampoCantidad() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: <Widget>[
            Text(
              'Cantidad',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(width: 16.0),
            InputQty.int(
              maxVal: 100,
              initVal: 1,
              minVal: 1,
              onQtyChanged: (val){
                setState(() {
                  _cantidad = val;
                });
              },
            )
          ],
        ),

      ],
    );
  }
}