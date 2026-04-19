import 'package:flutter/material.dart';

class ListaCompraPantallaVacia extends StatelessWidget {
  const ListaCompraPantallaVacia({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Text(
          'No hay productos todavía',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 16.0,),
        Text(
          'Pulsa el botón + para añadirlos',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    ),
    );
  }
}
