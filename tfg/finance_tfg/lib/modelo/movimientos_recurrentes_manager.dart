import 'dart:convert';
import 'dart:io';
import 'modelo.dart';

class MovimientosRecurrentesManager{

  static Future<File> _getArchivo(String cuentaId, [File? archivoMovimientos]) async {
    return AccesoBBDD.instancia.getMovimientosRecurrentes(cuentaId, archivoMovimientos);
  }

  static Future<List<Movimiento>> leerMovimientos(String cuentaId) async {
    try {
      final archivo = await _getArchivo(cuentaId);
      if (await archivo.exists()) {
        String contenido = await archivo.readAsString();
        List<dynamic> jsonList = jsonDecode(contenido);

        return jsonList.map((movimiento) => Movimiento.fromJson(movimiento)).toList();
      }
    } catch (e) {
      print("$e");
    }
    return [];
  }

  static Future<void> guardarMovimiento(Movimiento nuevoMovimiento, String cuentaId) async {
    List<Movimiento> listaActual = await leerMovimientos(cuentaId);

    listaActual.removeWhere((movimiento) => movimiento.getId() == nuevoMovimiento.getId());

    listaActual.add(nuevoMovimiento);
    
    String jsonString = jsonEncode(listaActual.map((movimiento) => movimiento.toJson()).toList());

    final file = await _getArchivo(cuentaId);
    await file.writeAsString(jsonString);
    await _getArchivo(cuentaId, file);
  }

  static Future<void> aniadirMovimiento({required Movimiento movimiento, required CuentaActual cuentaActual, bool guardarComoRecurrente = true}) async{
    final idCuenta = cuentaActual.getCuentaActual()?.cuenta.getId();

    double nuevoSaldoCuenta = cuentaActual.getCuentaActual()!.cuenta.getSaldo() + movimiento.getImporte();

    final String? movimientoId =  await AccesoBBDD.instancia.aniadirMovimiento(movimiento, idCuenta!);

    await AccesoBBDD.instancia.acutalizarSaldo(idCuenta, nuevoSaldoCuenta);
    cuentaActual.actualizarSaldoActual(nuevoSaldoCuenta);


    if(movimientoId != null && movimiento.getTipoRecurrencia() == TipoRecurrencia.recurrente && guardarComoRecurrente){
      movimiento.setId(movimientoId);
      await guardarMovimiento(movimiento, cuentaActual.getCuentaActual()!.cuenta.getId());
    }
  }

  static Future<void> revisarMovimientosRecurrentes(CuentaActual cuentaActual) async{
    final List<Movimiento> movimientos = await leerMovimientos(cuentaActual.getCuentaActual()!.cuenta.getId());

    final fechaActual = DateTime.now();

    for(Movimiento movimiento in movimientos){
      final recurrencia = movimiento.getRecurrencia();

      if (recurrencia == null) {
        continue;
      }

      final List<Movimiento> movimientosPendientes = recurrencia.generarMovimientosPendientes(movimiento, fechaActual);

      if (movimientosPendientes.isEmpty) {
        continue;
      }

      for(Movimiento movimientoPendiente in movimientosPendientes){
        await aniadirMovimiento(movimiento: movimientoPendiente, cuentaActual: cuentaActual, guardarComoRecurrente: false);
      }

      movimiento.setFecha(movimientosPendientes.last.getFecha());
      await guardarMovimiento(movimiento, cuentaActual.getCuentaActual()!.cuenta.getId());
    }
  }
}
