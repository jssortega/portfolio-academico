import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:intl/intl.dart';

import 'avatar_usuario.dart';


class LineaMovimientoDetallado extends StatelessWidget {

  final Movimiento movimiento;
  final bool mostrarFecha;
  final double balance;
  final Usuario? usuario;

  const LineaMovimientoDetallado({super.key, required this.movimiento, required this.mostrarFecha, required this.balance, required this.usuario});

  @override
  Widget build(BuildContext context) {
    final preferenciasVisuales = Provider.of<PreferenciasVisuales>(context);
    final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context);

    return Column(
      children: [
        if(mostrarFecha)
          Padding(
            padding: EdgeInsets.only(bottom: 10.h),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(DateFormat('dd/MM').format(movimiento.getFecha()), style: TextStyle(
                    fontSize: 24.sp, fontWeight: FontWeight.w500),),
                Card(
                    color: balance.isNegative ? Color(0xFFFFF1F2) : Color(0xFFECFDF5),
                    elevation: 5,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30.0.r),
                    ),
                    child: Padding(
                        padding: EdgeInsets.symmetric(
                            horizontal: 15.w, vertical: 5.h),
                        child: Row(
                          children: [
                            Text("Balance: ", style: TextStyle(color: balance.isNegative ? Color(0xFFF15858) : Color(0xFF24BF8B), fontSize: 20.sp, fontWeight: FontWeight.w500),),
                            Text(preferenciasVisuales.getOcultarImportes() ? "****" : formatearImporte(preferenciasDivisa.calcularImporte(balance)), style: TextStyle(color: balance.isNegative ? Color(0xFFF15858) : Color(0xFF24BF8B), fontSize: 20.sp, fontWeight: FontWeight.w500),),
                            Text(preferenciasDivisa.getsimboloActual(), style: TextStyle(color: balance.isNegative ? Color(0xFFF15858) : Color(0xFF24BF8B), fontSize: 20.sp, fontWeight: FontWeight.w500))
                          ],
                        )
                    )
                )
              ],
            ),
          ),
        Row(
          children: [
            Column(
              children: [
                AvatarUsuario(
                  imagenPerfil: usuario?.getImagenPerfil() ?? "",
                  radio: 24.r,
                  iconSize: 24.r,
                ),
                Text(usuario?.getNombreUsuario() ?? "Usuario", style: TextStyle(color: Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w500),)
              ],
            ),
            SizedBox(width: 5.w,),
            Expanded(
              child: Card(
                color: Colors.white,
                elevation: 5,
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 15.w, vertical: 20.h),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(movimiento.getCategoria().icono, size: 24.sp, color: movimiento.getCategoria().colorIcono),
                          SizedBox(width: 5.w,),
                          Text(movimiento.getCategoria().nombre(context), style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w600),),
                        ],
                      ),
                      Row(
                        children: [
                          Text(preferenciasVisuales.getOcultarImportes() ? "****" : formatearImporte(preferenciasDivisa.calcularImporte(movimiento.getImporte())), style: TextStyle(color: movimiento.getImporte().isNegative ? Color(0xFFF15858) : Color(0xFF24BF8B), fontSize: 20.sp, fontWeight: FontWeight.w500)),
                          Text(preferenciasDivisa.getsimboloActual(), style: TextStyle(color: movimiento.getImporte().isNegative ? Color(0xFFF15858) : Color(0xFF24BF8B), fontSize: 20.sp, fontWeight: FontWeight.w500))
                        ],
                      ),
                      InkWell(
                        onTap: (){
                          Navigator.push(
                            context,
                              MaterialPageRoute(
                                builder: (context){
                                  if(movimiento.getTipoRecurrencia() == TipoRecurrencia.recurrente) {
                                    return DetalleMovimientoRecurrentePantalla(movimiento: movimiento,);
                                  } else{
                                    return DetalleMovimientoUnicoPantalla(movimiento: movimiento);
                                  }
                                }
                              )
                            );
                        },
                        child: Text("+Detalles", style: TextStyle(color: Color(0xFF2563EB), fontSize: 16.sp, decoration: TextDecoration.underline)),
                      ),
                    ],
                  )
                )
              ),
            )

          ],
        ),
        SizedBox(height: 15.h,),
      ],
    );
  }
}
