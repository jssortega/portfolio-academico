import 'package:flutter/material.dart';

class Raqueta extends StatelessWidget {
  final double anchura;
  final double altura;
  Raqueta({Key? key, this.anchura = 100, this.altura = 25});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: anchura,
      height: altura,
      decoration: const BoxDecoration(
        color: Colors.indigo,
      ),
    );
  }
}