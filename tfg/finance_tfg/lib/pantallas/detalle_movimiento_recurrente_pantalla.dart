import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:intl/intl.dart';

class DetalleMovimientoRecurrentePantalla extends StatelessWidget {
  final Movimiento movimiento;

  const DetalleMovimientoRecurrentePantalla({super.key, required this.movimiento});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: Padding(
        padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 30.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.start,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(capitalizarPrimera(movimiento.getTipoMovimiento().name), style: TextStyle(color: Color(0xFF67778D), fontSize: 28.sp, fontWeight: FontWeight.w500),),
                    Icon(Icons.sync, color: Color(0xFF67778D), size: 28.sp,)
                  ],
                ),

                CardSaldoActual(),

                SizedBox(height: 20.h,),
                Text(DateFormat('dd/MM/yyyy').format(movimiento.getFecha()), style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w500),),

                SizedBox(height: 30.h,),

                construirLineaInformacion(Icons.cases, Color(0xFFD1FAE5), Color(0xFF059669), AppLocalizations.of(context)!.categoriaDetalleMovimiento, movimiento.getCategoria().nombre(context)),
                construirLineaInformacion(Icons.calendar_today, Color(0xFFFEF3C7), Color(0xFFEA580C), AppLocalizations.of(context)!.frecuenciaDetalleMovimiento, capitalizarPrimera(movimiento.getRecurrencia()!.name)),
                construirLineaInformacion(Icons.calendar_month, Color(0xFFDBEAFE), Color(0xFF2563EB), AppLocalizations.of(context)!.proximoDetalleMovimiento, "10/04/2026"),

                SizedBox(height: 30.h,),

                construirLineaFecha(AppLocalizations.of(context)!.inicioDetalleMovimiento, AppLocalizations.of(context)!.fechaDetalleMovimiento, Color(0xFF67778D)),
                construirLineaFecha(DateFormat('dd/MM/yyyy').format(movimiento.getFecha()), "10/12/2026", Colors.black),

              ],
            ),

            Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text("¿Ha terminado el ingreso?", style: TextStyle(color: Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w500),),
                SizedBox(height: 5.h,),
                BotonPrincipal(
                  texto: "Finalizar ingreso",
                  onPressed: (){},
                  color: Color(0xFFF15858),
                )
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget construirLineaInformacion(IconData icono, Color cardBackgrounColor, Color iconColor, String info, String nombre){
    return Padding(
      padding: EdgeInsets.only(bottom: 10.h),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Card(
                elevation: 5,
                color: cardBackgrounColor,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20.0.r),
                ),
                child: Padding(
                  padding: EdgeInsets.all(6.0.sp),
                  child: Icon(icono, color: iconColor, size: 24.sp,),
                )
              ),
              SizedBox(width: 5.w,),
              Text(info, style: TextStyle(color: Color(0xFF67778D), fontSize: 28.sp, fontWeight: FontWeight.w500),)
            ],
          ),
          Text(nombre, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w500),)
        ],
      ),
    );
  }

  Widget construirLineaFecha(String texto1, String texto2, Color color){
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(texto1, style: TextStyle(color: color, fontSize: 28.sp, fontWeight: FontWeight.w500),),
        Text(texto2, style: TextStyle(color: color, fontSize: 28.sp, fontWeight: FontWeight.w500),)
      ],
    );
  }
}
