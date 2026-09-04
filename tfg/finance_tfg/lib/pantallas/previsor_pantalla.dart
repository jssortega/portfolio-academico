import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:intl/intl.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/utils/global.dart';


class PrevisorPantalla extends StatefulWidget {
  const PrevisorPantalla({super.key});

  @override
  State<PrevisorPantalla> createState() => _PrevisorPantallaState();
}

class _PrevisorPantallaState extends State<PrevisorPantalla> {

  int? groupValueTipo = 0;
  int? groupValueRecurrencia = 0;

  int recurrenciaSeleccionada = 0;

  TextEditingController importe = TextEditingController();

  DateTime _fechaUnica = DateTime.now();
  int minYear = 2020;
  int maxYear = 2030;

  DateTime _fechaInicio = DateTime.now();
  DateTime _fechaFin = DateTime.now();

  bool valorSwitch = true;

  bool estaDesabilitado = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Previsor", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.symmetric(vertical: 30.h,horizontal: 30.w),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      LineaTexto(texto: "¿Cuándo quiere hacer la previsión?"),

                      Padding(
                        padding: EdgeInsets.only(bottom: 4.h),
                        child: Text("Seleccione el rango de tiempo para el análisis", style: TextStyle(color: Color(0xFF67778D), fontSize: 16.sp, fontWeight: FontWeight.w500),),
                      ),

                      construirSelector("Fecha", "Periodo", groupValueRecurrencia, (value){setState(() {groupValueRecurrencia = value;});}),

                      SizedBox(height: 20.h,),

                      if(groupValueRecurrencia==0) ...[
                        LineaTexto(texto: "Seleccione fecha:"),
                        Container(
                          decoration: BoxDecoration(
                            border: Border.all(width: 1.w),
                          ),
                          height: 40.h,
                          child: InkWell(
                            onTap: () {
                              _selectDate(context, initialDate: _fechaUnica, onSelected: (fecha) {_fechaUnica = fecha; }, );
                            },
                            child:Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: <Widget>[
                                Icon(Icons.calendar_month),
                                Text(DateFormat.yMMMd().format(_fechaUnica)),
                                Icon(Icons.arrow_drop_down,color: Theme.of(context).brightness == Brightness.light? Colors.grey.shade700: Colors.white70),
                              ],
                            ),
                          ),
                        ),
                      ] else ...[
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            LineaTexto(texto: "Desde:"),
                            LineaTexto(texto: "Hasta:")
                          ],
                        ),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                border: Border.all(width: 1.w),
                              ),
                              height: 40.h,
                              child: InkWell(
                                onTap: () {
                                  _selectDate(context, initialDate: _fechaInicio, onSelected: (fecha) {_fechaInicio = fecha;}, );
                                },
                                child:Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: <Widget>[
                                    Icon(Icons.calendar_month),
                                    Text(DateFormat.yMMMd().format(_fechaInicio)),
                                    Icon(Icons.arrow_drop_down),
                                  ],
                                ),
                              ),
                            ),
                            Container(
                              decoration: BoxDecoration(
                                border: Border.all(width: 1.w),
                              ),
                              height: 40.h,
                              child: InkWell(
                                onTap: () {
                                  _selectDate(context, initialDate: _fechaFin, onSelected: (fecha) {_fechaFin = fecha;}, );
                                },
                                child:Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: <Widget>[
                                    Icon(Icons.calendar_month),
                                    Text(DateFormat.yMMMd().format(_fechaFin)),
                                    Icon(Icons.arrow_drop_down),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],

                      SizedBox(height: 20.h,),

                      LineaTexto(texto: "¿Qué quiere simular?"),

                      construirSelector("Gasto", "Ingreso", groupValueTipo, (value){setState(() {groupValueTipo = value;});}),

                      SizedBox(height: 20.h,),

                      LineaTextfieldImporte(textController: importe, comprobarError: (error){setState(() {estaDesabilitado = error;});}),

                      SizedBox(height: 20.h,),

                      if(groupValueRecurrencia == 1) ...[
                        LineaTexto(texto: "Seleccione recurrencia"),

                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: [
                              LineaChips(texto: "Diario", indice: 0, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                              LineaChips(texto: "Semanal", indice: 1, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                              LineaChips(texto: "Mensual", indice: 2, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                              LineaChips(texto: "Anual", indice: 3, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                            ],
                          ),
                        ),

                        SizedBox(height: 20.h,),

                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),

          Padding(
            padding: EdgeInsets.symmetric(vertical: 15.h, horizontal: 30.w),
            child: BotonPrincipal(
              texto: "Calcular previsión",
              onPressed: (){
                final bool esPeriodo = groupValueRecurrencia == 1;

                final DateTime fechaObjetivo = _fechaUnica;
                final DateTime fechaInicio = _fechaInicio;
                final DateTime fechaFin = _fechaFin;

                double importePrevision = double.tryParse(importe.text) ?? 0;
                final bool esGasto = groupValueTipo == 0;
                importePrevision = esGasto ? -importePrevision : importePrevision;

                if(esPeriodo){
                  Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context){
                            return ResultadoPrevisorPantalla(fechaObjetivo: fechaInicio, importe: importePrevision, esGasto: esGasto, fechaFin: fechaFin, esPeriodo: esPeriodo, recurrenciaSeleccionada: recurrenciaSeleccionada,);
                          }
                      )
                  );
                } else{
                  Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context){
                            return ResultadoPrevisorPantalla(fechaObjetivo: fechaObjetivo, importe: importePrevision, esGasto: esGasto, esPeriodo: esPeriodo,);
                          }
                      )
                  );
                }

              },
              desabilitado: estaDesabilitado,
            ),
          ),
        ],
      )
    );
  }

  Widget construirSelector(String textoElemento1, String textoElemento2, int? seleccion, ValueChanged<int?> onChanged){
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        SizedBox(
          width: 300.w,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10.r),
            child: CupertinoSlidingSegmentedControl<int>(
              backgroundColor: Color(0xFFF0F2F5),
              thumbColor: Colors.white,
              groupValue: seleccion,
              children: {
                0: construirSegmento(textoElemento1, seleccion == 0),
                1: construirSegmento(textoElemento2, seleccion == 1),
              },
              onValueChanged: (value) {
                onChanged(value);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget construirSegmento(String text, bool isSelected) {
    return ClipRRect(
        borderRadius: BorderRadius.circular(25.r),
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 10.h),
          child: Text(
            text,
            style: TextStyle(
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? Colors.black : Colors.blueGrey,
            ),
          ),
        )
    );
  }

  Future<void> _selectDate(BuildContext context, {required DateTime initialDate, required Function(DateTime) onSelected, DateTime? firstDate,}) async {
    final DateTime fechaMinima = firstDate ?? DateTime(minYear);

    final DateTime initialDateSegura = initialDate.isBefore(fechaMinima) ? fechaMinima : initialDate;

    final DateTime? picked = await showDatePicker(context: context, initialDate: initialDateSegura, firstDate: fechaMinima, lastDate: DateTime(maxYear),);

    if (picked != null) {
      setState(() {
        onSelected(picked);
      });
    }
  }

}
