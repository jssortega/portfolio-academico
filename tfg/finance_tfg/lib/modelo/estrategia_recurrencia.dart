import 'modelo.dart';
import 'package:jiffy/jiffy.dart';

abstract class EstrategiaRecurrencia {
  const EstrategiaRecurrencia();

  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual);
}

class EstrategiaDiaria extends EstrategiaRecurrencia {
  const EstrategiaDiaria();

  @override
  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual) {
    List<Movimiento> movimientos = [];

    var fechaMovimiento = Jiffy.parseFromDateTime(movimiento.getFecha());
    var fechaHoy = Jiffy.parseFromDateTime(fechaActual);

    num diasPasados = fechaHoy.diff(fechaMovimiento, unit: Unit.day);

    for(int i=1; i<=diasPasados; i++){
      var nuevaFecha = fechaMovimiento.add(days: i);
      Movimiento nuevoMovimiento = movimiento.copiaConFecha(nuevaFecha.dateTime);
      movimientos.add(nuevoMovimiento);
    }

    return movimientos;
  }
}

class EstrategiaSemanal extends EstrategiaRecurrencia {
  const EstrategiaSemanal();

  @override
  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual) {
    List<Movimiento> movimientos = [];

    var fechaMovimiento = Jiffy.parseFromDateTime(movimiento.getFecha());
    var fechaHoy = Jiffy.parseFromDateTime(fechaActual);

    num semanasPasadas = fechaHoy.diff(fechaMovimiento, unit: Unit.week);

    for(int i=1; i<=semanasPasadas; i++){
      var nuevaFecha = fechaMovimiento.add(weeks: i);
      Movimiento nuevoMovimiento = movimiento.copiaConFecha(nuevaFecha.dateTime);
      movimientos.add(nuevoMovimiento);
    }

    return movimientos;
  }
}

class EstrategiaMensual extends EstrategiaRecurrencia {
  const EstrategiaMensual();

  @override
  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual) {
    List<Movimiento> movimientos = [];

    var fechaMovimiento = Jiffy.parseFromDateTime(movimiento.getFecha());
    var fechaHoy = Jiffy.parseFromDateTime(fechaActual);

    num mesesPasados = fechaHoy.diff(fechaMovimiento, unit: Unit.month);

    for(int i=1; i<=mesesPasados; i++){
      var nuevaFecha = fechaMovimiento.add(months: i);
      Movimiento nuevoMovimiento = movimiento.copiaConFecha(nuevaFecha.dateTime);
      movimientos.add(nuevoMovimiento);
    }

    return movimientos;
  }
}

class EstrategiaAnual extends EstrategiaRecurrencia {
  const EstrategiaAnual();

  @override
  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual) {
    List<Movimiento> movimientos = [];

    var fechaMovimiento = Jiffy.parseFromDateTime(movimiento.getFecha());
    var fechaHoy = Jiffy.parseFromDateTime(fechaActual);

    num aniosPasados = fechaHoy.diff(fechaMovimiento, unit: Unit.year);

    for(int i=1; i<=aniosPasados; i++){
      var nuevaFecha = fechaMovimiento.add(years: i);
      Movimiento nuevoMovimiento = movimiento.copiaConFecha(nuevaFecha.dateTime);
      movimientos.add(nuevoMovimiento);
    }

    return movimientos;
  }
}