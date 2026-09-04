import 'package:flutter/material.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class FinanceCuentaApp extends StatelessWidget {
  const FinanceCuentaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<CuentaActual>(
      builder: (context, cuentaActual, _) {
        return StreamBuilder<List<CuentaConRol>>(
          stream: AccesoBBDD.instancia.getCuentasUsuario(),
          builder: (context, snapshotCuentas) {
            if (snapshotCuentas.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }

            if (snapshotCuentas.hasError) {
              return const Scaffold(
                body: Center(
                  child: Text("Error al cargar las cuentas"),
                ),
              );
            }

            final cuentas = snapshotCuentas.data ?? [];

            if (cuentas.isEmpty || cuentaActual.getCuentaActual() == null) {
              return const CuentasPantalla();
            }
            return const FinancePaginaPrincipal();
          },
        );
      },
    );
  }
}