import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';

class LineaChips extends StatelessWidget {
  final String texto;
  final int indice;
  final int chipSeleccionado;
  final Function(int) onChipSeleccionado;

  const LineaChips({super.key, required this.texto, required this.indice, required this.chipSeleccionado, required this.onChipSeleccionado});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(right: 4.w),
      child: FilterChip(
        label: Text(texto, style: chipSeleccionado == indice ? const TextStyle(color: Colors.white) : const TextStyle(color: Color(0xFF828FA2)),),
        selected: chipSeleccionado == indice,
        onSelected: (_){
          onChipSeleccionado(indice);
        },
        elevation: 5,
        backgroundColor: Colors.white,
        selectedColor: const Color(0xFF1E293B),
        shape: const StadiumBorder(),
        showCheckmark: false,
      ),
    );
  }
}
