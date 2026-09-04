import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';

class LineaTextfieldContrasena extends StatefulWidget {
  final TextEditingController textController;

  const LineaTextfieldContrasena({super.key, required this.textController});


  @override
  State<LineaTextfieldContrasena> createState() => _LineaTextfieldContrasenaState();
}

class _LineaTextfieldContrasenaState extends State<LineaTextfieldContrasena> {
  bool _isOculto = true;

  @override
  Widget build(BuildContext context) {
    return TextField(
      obscureText: _isOculto,
      controller: widget.textController,
      decoration: InputDecoration(
          border: OutlineInputBorder(
              borderSide: (BorderSide(width: 1.w, color: Colors.black))
          ),
          prefixIcon: Icon(Icons.lock),
          suffixIcon: IconButton(
              onPressed: (){setState(() {_isOculto = !_isOculto;});},
              icon: Icon(_isOculto ? Icons.visibility_off : Icons.visibility)
          ),
          filled: true,
          fillColor: Colors.white,
          hintText: "*******************",
          hintStyle: const TextStyle(color: Color(0xFF67778D)),
          focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.black, width: 2.w)
          )
      ),
    );
  }
}
