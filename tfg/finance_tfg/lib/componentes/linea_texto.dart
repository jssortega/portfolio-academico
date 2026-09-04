import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';

class LineaTexto extends StatelessWidget {
  final String texto;
  const LineaTexto({super.key, required this.texto});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: 4.h),
      child: Text(texto, style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600),),
    );
  }
}
