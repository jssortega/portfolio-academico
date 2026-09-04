import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';

class BotonPrincipal extends StatelessWidget {

  final String texto;
  final double padding;
  final VoidCallback onPressed;
  final Color color;
  final bool desabilitado;

  const BotonPrincipal({super.key, required this.texto, this.padding = 20, required this.onPressed, this.color = const Color(0xFF1E293B), this.desabilitado = false});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton(
              style: ElevatedButton.styleFrom(backgroundColor: color, padding: EdgeInsets.symmetric(vertical: padding.h), side: BorderSide.none),
              onPressed: !desabilitado ? onPressed : null,
              child: Text(texto, style: TextStyle(color: Colors.white, fontSize: 20.sp),)
          ),
        ),
      ],
    );
  }
}
