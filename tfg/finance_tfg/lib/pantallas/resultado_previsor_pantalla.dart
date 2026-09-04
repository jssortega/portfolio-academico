import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/previsor_manager.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class ResultadoPrevisorPantalla extends StatelessWidget {
  final DateTime fechaObjetivo;
  final double importe;
  final bool esGasto;
  final DateTime? fechaFin;
  final bool esPeriodo;
  final int? recurrenciaSeleccionada;

  const ResultadoPrevisorPantalla({super.key, required this.fechaObjetivo, required this.importe, required this.esGasto, this.fechaFin, required this.esPeriodo, this.recurrenciaSeleccionada});

  @override
  Widget build(BuildContext context){
    final cuentaActual = Provider.of<CuentaActual>(context, listen: false);
    String cuentaId = cuentaActual.getCuentaActual()!.cuenta.getId();

    final double saldoActual = cuentaActual.getCuentaActual()?.cuenta.getSaldo() ?? 0.0;

    final PrevisorManager previsorManager = PrevisorManager();

    return Scaffold(
        appBar: AppBar(
          title: Text("Resultados", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
          centerTitle: true,
        ),
        body: FutureBuilder<double>(
          future: previsorManager.obtenerSaldoSimulado(fechaObjetivo, saldoActual, importe, cuentaId, esPeriodo, fechaFin: fechaFin, recurrenciaSeleccionada: recurrenciaSeleccionada),
          builder: (context, asyncSnapshot) {

            if (asyncSnapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }

            if (asyncSnapshot.hasError) {
              return Center(child: Text("Error al calcular la previsión"));
            }

            final saldoEstimado = asyncSnapshot.data ?? 0.0;

            return SingleChildScrollView(
              child: Column(
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: double.infinity,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            LineaTexto(texto: "Saldo estimado el ${DateFormat('dd/MM/yyyy').format(fechaObjetivo)}"),
                            Card(
                                color: Color(0xFFFFFFFF),
                                elevation: 5,
                                child: Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 50.w, vertical: 20.h),
                                  child: Column(
                                    children: [
                                      Row(
                                        mainAxisSize: MainAxisSize.min,
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Text("Saldo estimado:", style: TextStyle(color: Color(0xFF67778D), fontSize: 16.sp ,fontWeight: FontWeight.w600),)
                                        ],
                                      ),
                                      Row(
                                        mainAxisSize: MainAxisSize.min,
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Text(formatearImporte(saldoEstimado), style: TextStyle(fontSize: 32.sp, fontWeight: FontWeight.bold),),
                                          Icon(Icons.euro, size: 32.sp)
                                        ],
                                      )
                                    ],
                                  ),
                                )
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  Padding(
                    padding: EdgeInsets.only(left: 16.w, top: 32.h),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        LineaTexto(texto: "Tus variables:"),

                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: [
                              construirCardVariables(texto: DateFormat('dd/MM/yyyy').format(fechaObjetivo)),
                              esGasto ? construirCardVariables(texto: "-${formatearImporte(importe)}", icono: Icons.euro) : construirCardVariables(texto: "+${formatearImporte(importe)}", icono: Icons.euro),
                              ?fechaFin != null ? construirCardVariables(texto: DateFormat('dd/MM/yyyy').format(fechaFin!)) : null
                            ],
                          ),
                        ),

                        SizedBox(height: 32.h,),

                        LineaTexto(texto: "Gráfica"),

                        FutureBuilder<List<double>>(
                          future: previsorManager.obtenerImportesGrafica(cuentaId, fechaObjetivo, saldoActual, importe, esPeriodo, fechaFin: fechaFin, recurrenciaSeleccionada: recurrenciaSeleccionada),
                          builder: (context, snapshotGrafica) {
                            if (snapshotGrafica.connectionState == ConnectionState.waiting) {
                              return const Center(child: CircularProgressIndicator());
                            }

                            if (snapshotGrafica.hasError) {
                              return const Text("Error al cargar la gráfica");
                            }

                            final importesGrafica = snapshotGrafica.data ?? [];

                            if (importesGrafica.isEmpty) {
                              return const Text("No hay datos para mostrar");
                            }

                            return PrevisionGrafica(importesGrafica: importesGrafica, fechaObjetivo: fechaObjetivo,);
                          },
                        ),
                      ],
                    ),
                  )
                ],
              ),
            );
          }
        )
    );
  }

  Widget construirCardVariables({required String texto, IconData? icono}){
    return Card(
        color: Colors.white,
        elevation: 5,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(30.0.r),
        ),
        child: Padding(
          padding: EdgeInsets.symmetric(
              horizontal: 15.w, vertical: 5.h),
          child: Row(
            children: [
              Text(texto, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w600),),
              if (icono != null) ...[
                Icon(icono, size: 20.sp, fontWeight: FontWeight.w500,),
              ]
            ],
          ),
        )
    );
  }
}
