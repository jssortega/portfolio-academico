import 'package:finance_tfg/utils/global.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class LineaMovimiento extends StatelessWidget {
  final IconData iconoCategoria;
  final String nombreCategoria;
  final String fecha;
  final double importe;
  final Color iconoCategoriaColor;
  final String tipo;
  final TipoRecurrencia tipoRecurrencia;

  const LineaMovimiento({super.key, required this.iconoCategoria, required this.nombreCategoria, required this.fecha, required this.importe, required this.iconoCategoriaColor, required this.tipo, required this.tipoRecurrencia});

  @override
  Widget build(BuildContext context) {
    final bool esGasto = tipo == "gasto";
    final Color color = esGasto ? const Color(0xFFF15858) : const Color(0xFF24BF8B);
    final preferenciasVisuales = Provider.of<PreferenciasVisuales>(context);
    final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context);

    return Padding(
      padding: EdgeInsets.symmetric(vertical: 2.h, horizontal: 32.w),
      child: Card(
        color: Colors.white,
        elevation: 5,
        child: Padding(
          padding: EdgeInsets.all(8.sp),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(iconoCategoria, color: iconoCategoriaColor,),
                  SizedBox(width: 8.w,),
                  Column(
                    children: [
                      Text(nombreCategoria, style: TextStyle( fontSize: 16.sp ,fontWeight: FontWeight.w600),),
                      Text(fecha, style: TextStyle( fontSize: 16.sp ,fontWeight: FontWeight.w400))
                    ],
                  )
                ],
              ),
              Row(
                children: [
                  tipoRecurrencia == TipoRecurrencia.recurrente ? Icon(Icons.autorenew, color: Color(0xFF828FA2)) : Container(),
                  Text(preferenciasVisuales.getOcultarImportes() ? "****" : formatearImporte(preferenciasDivisa.calcularImporte(importe)), style: TextStyle(color: color, fontSize: 20.sp ,fontWeight: FontWeight.w600)),
                  Text(preferenciasDivisa.getsimboloActual(), style: TextStyle(color: color, fontSize: 20.sp, fontWeight: FontWeight.w600))
                ],
              )
            ],
          ),
        ),
      ),
    );
  }
}
