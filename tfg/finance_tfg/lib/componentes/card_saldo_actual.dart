import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class CardSaldoActual extends StatelessWidget {
  const CardSaldoActual({super.key});

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<CuentaActual>(context);
    final preferenciasVisuales = Provider.of<PreferenciasVisuales>(context);
    final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context);

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Card(
            color: Color(0xFFFFFFFF),
            elevation: 5,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 50.w, vertical: 20.h),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(AppLocalizations.of(context)!.saldoActual, style: TextStyle(color: Color(0xFF67778D), fontSize: 16.sp ,fontWeight: FontWeight.w600),)
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(preferenciasVisuales.getOcultarImportes() ? "****" : formatearImporte(preferenciasDivisa.calcularImporte(manager.getCuentaActual()!.cuenta.getSaldo())), style: TextStyle(fontSize: 32.sp, fontWeight: FontWeight.bold),),
                      Text(preferenciasDivisa.getsimboloActual(), style: TextStyle(fontSize: 32.sp, fontWeight: FontWeight.w600))
                    ],
                  )
                ],
              ),
            )
        )
      ],
    );
  }
}
