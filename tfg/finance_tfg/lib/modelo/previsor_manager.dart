import 'package:finance_tfg/modelo/modelo.dart';
import 'package:jiffy/jiffy.dart';

class PrevisorManager {

  Future<double> obtenerSaldoSimulado(DateTime fechaObjetivo, double saldoActual, double importeIntroducido, String cuentaId, bool esPeriodo, {DateTime? fechaFin, int? recurrenciaSeleccionada}) async {
    double saldoPrevisto = saldoActual;

    final DateTime fechaLimite = esPeriodo ? fechaFin! : fechaObjetivo;
    List<Movimiento> movimientosTotales = await obtenerMovimientosTotales(cuentaId, fechaLimite);

    for(Movimiento movimiento in movimientosTotales){
      saldoPrevisto += movimiento.getImporte();
    }

    if(!esPeriodo){
      saldoPrevisto += importeIntroducido;
    }else{
      switch (recurrenciaSeleccionada){
        case 0:
          saldoPrevisto = obtenerImportePeriodo(saldoPrevisto, importeIntroducido, Unit.day, fechaObjetivo, fechaFin!);
          break;
        case 1:
          saldoPrevisto = obtenerImportePeriodo(saldoPrevisto, importeIntroducido, Unit.week, fechaObjetivo, fechaFin!);
          break;
        case 2:
          saldoPrevisto = obtenerImportePeriodo(saldoPrevisto, importeIntroducido, Unit.month, fechaObjetivo, fechaFin!);
          break;
        case 3:
          saldoPrevisto = obtenerImportePeriodo(saldoPrevisto, importeIntroducido, Unit.year, fechaObjetivo, fechaFin!);
          break;
      }
    }


    return saldoPrevisto;
  }

  Future<List<double>> obtenerImportesGrafica(String cuentaId, DateTime fecha, double saldoActual, double importeIntroducido, bool esPeriodo, {DateTime? fechaFin, int? recurrenciaSeleccionada}) async {
    List<double> importesGrafica = [];

    var fechaInicio = fechaFin == null ? Jiffy.parseFromDateTime(fecha).subtract(days: 7).dateTime : fecha;
    var fechaFinal = fechaFin ?? Jiffy.parseFromDateTime(fecha).add(days: 7).dateTime;
    var fechaDiaria = fechaInicio;

    double saldoSimulado = saldoActual;
    List<Movimiento> movimientosTotales = await obtenerMovimientosTotales(cuentaId, fechaFinal);

    final diferenciaDias = Jiffy.parseFromDateTime(fechaFinal).diff(Jiffy.parseFromDateTime(fechaInicio), unit: Unit.day);

    for(int i=0; i < diferenciaDias + 1; i++){

      for(Movimiento movimiento in movimientosTotales){
        DateTime fechaMovimiento = movimiento.getFecha();

        if(Jiffy.parseFromDateTime(fechaMovimiento).isSame(Jiffy.parseFromDateTime(fechaDiaria), unit: Unit.day,)){
          saldoSimulado += movimiento.getImporte();
        }

      }

      if (esPeriodo && tocaAplicarImporte(fechaDiaria, fechaInicio, recurrenciaSeleccionada)) {
        saldoSimulado += importeIntroducido;
      } else if(!esPeriodo && Jiffy.parseFromDateTime(fecha).isSame(Jiffy.parseFromDateTime(fechaDiaria), unit: Unit.day,)){
        saldoSimulado += importeIntroducido;
      }

      importesGrafica.add(saldoSimulado);
      fechaDiaria = Jiffy.parseFromDateTime(fechaDiaria).add(days: 1).dateTime;
    }

    return importesGrafica;
  }

  Future<List<Movimiento>> obtenerMovimientosTotales(String cuentaId, DateTime fechaObjetivo,) async {
    List<Movimiento> movimientos = await MovimientosRecurrentesManager.leerMovimientos(cuentaId);
    List<Movimiento> movimientosTotales = [];

    for(Movimiento movimiento in movimientos) {
      final recurrencia = movimiento.getRecurrencia();

      final List<Movimiento> movimientosPendientes = recurrencia?.generarMovimientosPendientes(movimiento, fechaObjetivo) ?? [];
      movimientosTotales.addAll(movimientosPendientes);
    }

    movimientosTotales.sort((Movimiento a, Movimiento b)=>a.getFecha().compareTo(b.getFecha()));

    return movimientosTotales;
  }

  double obtenerImportePeriodo(double saldoPrevisto, double importeIntroducido, Unit unidad, DateTime fechaInicio, DateTime fechaFin){
    final diferencia = Jiffy.parseFromDateTime(fechaFin).diff(Jiffy.parseFromDateTime(fechaInicio), unit: unidad);

    for(int i=0; i<=diferencia; i++){
      saldoPrevisto += importeIntroducido;
    }

    return saldoPrevisto;
  }

  bool tocaAplicarImporte(DateTime fechaDiaria, DateTime fechaInicio, int? recurrenciaSeleccionada) {
    final diferenciaDias = Jiffy.parseFromDateTime(fechaDiaria).diff(Jiffy.parseFromDateTime(fechaInicio), unit: Unit.day);

    switch (recurrenciaSeleccionada) {
      case 0:
        return true;

      case 1:
        return diferenciaDias % 7 == 0;

      case 2:
        return fechaDiaria.day == fechaInicio.day;

      case 3:
        return fechaDiaria.day == fechaInicio.day && fechaDiaria.month == fechaInicio.month;

      default:
        return false;
    }
  }

}