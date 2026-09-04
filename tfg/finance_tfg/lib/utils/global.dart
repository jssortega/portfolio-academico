export 'package:flutter_screenutil/flutter_screenutil.dart';
export 'package:finance_tfg/l10n/app_localizations.dart';

String capitalizarPrimera(String texto) {
  if (texto.isEmpty) return texto;
  return texto[0].toUpperCase() + texto.substring(1);
}

String formatearImporte(double importe) {
  if (importe % 1 == 0) {
    return importe.toInt().toString();
  }

  return importe.toStringAsFixed(2);
}