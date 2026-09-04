import 'package:flutter/material.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class MovimientosProvider extends StatelessWidget {
  final Widget child;

  const MovimientosProvider({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    final cuentaActual = Provider.of<CuentaActual>(context);

    final cuentaSeleccionada = cuentaActual.getCuentaActual();

    if (cuentaSeleccionada == null) {
      return Provider<List<Movimiento>?>.value(
        value: null,
        child: child,
      );
    }

    final idCuenta = cuentaSeleccionada.cuenta.getId();

    return StreamProvider<List<Movimiento>?>(
      key: ValueKey(idCuenta),
      initialData: null,
      create: (_) => AccesoBBDD.instancia.getMovimientos(idCuenta),
      catchError: (_, error) {
        debugPrint('Error cargando movimientos: $error');
        return <Movimiento>[];
      },
      child: child,
    );
  }
}