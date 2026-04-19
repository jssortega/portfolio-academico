import 'package:flutter/material.dart';

class Pelota extends StatelessWidget {
  final double diametro;
  Pelota({Key? key, this.diametro = 50});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: diametro,
      height: diametro,
      decoration: const BoxDecoration(
        color: Colors.red,
        shape: BoxShape.circle,
      ),
    );
  }
}