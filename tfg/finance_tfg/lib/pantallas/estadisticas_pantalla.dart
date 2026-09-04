import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/componentes/componentes.dart';

class EstadisticasPantalla extends StatelessWidget {
  const EstadisticasPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.estadisticasTitulo, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body:  SingleChildScrollView(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 20.w),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              LineaTexto(texto: AppLocalizations.of(context)!.resumenMes),
              SizedBox(height: 8.h,),
              Container(
                  decoration: const BoxDecoration(color: Colors.white, borderRadius: BorderRadius.all(Radius.circular(18)),),
                  child: ResumenMesGrafica()
              ),
              SizedBox(height: 12.h,),
              LineaTexto(texto: AppLocalizations.of(context)!.gastosPorCategoria),
              Container(
                  decoration: const BoxDecoration(color: Colors.white, borderRadius: BorderRadius.all(Radius.circular(18)),),
                  child: PieChartSample2()
              ),
            ],
          ),
        )
      ),
    );
  }
}
