import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';

class LineaTextfield extends StatelessWidget {
  final TextEditingController textController;
  final String? hintText;
  final IconData prefixIcon;


  const LineaTextfield({super.key, required this.textController, this.hintText, required this.prefixIcon});

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: textController,
      decoration: InputDecoration(
          border: OutlineInputBorder(
              borderSide: (BorderSide(width: 1.w, color: Colors.black))
          ),
          prefixIcon: Icon(prefixIcon),
          filled: true,
          fillColor: Colors.white,
          hintText: hintText,
          hintStyle: const TextStyle(color: Color(0xFF67778D)),
          focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.black, width: 2.w)
          )
      ),
    );
  }
}
