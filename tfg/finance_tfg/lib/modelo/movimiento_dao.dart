import 'dart:io';
import 'movimiento.dart';

abstract class MovimientoDAO{
  Future<String?> aniadirMovimiento(Movimiento movimiento, String cuentaId);

  Stream<List<Movimiento>> getMovimientos(String cuentaId);

  Future<File> getMovimientosRecurrentes(String cuentaId, File? movimientos);
}