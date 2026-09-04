import 'package:finance_tfg/modelo/modelo.dart';
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:intl/intl.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';

class AnadirMovimientoPantalla extends StatefulWidget {
  const AnadirMovimientoPantalla({super.key});

  @override
  State<AnadirMovimientoPantalla> createState() => _AnadirMovimientoPantallaState();
}
typedef MenuEntry = DropdownMenuEntry<String>;

class _AnadirMovimientoPantallaState extends State<AnadirMovimientoPantalla> {

  int? groupValueTipo = 0;
  int? groupValueRecurrencia = 0;

  TextEditingController importe = TextEditingController();

  Categoria categoriaSeleccionada = Categoria.ocio;

  DateTime fechaSeleccionada = DateTime.now();
  int minYear = 2010;
  int maxYear = 2030;

  void _onDateChange(DateTime newDate) {
    setState(() {
      fechaSeleccionada = newDate;
    });
  }

  int recurrenciaSeleccionada = 0;

  bool estaDesabilitado = false;

  @override
  void dispose() {
    importe.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              disabledColor: Colors.pink,
              onPressed: !estaDesabilitado ? () async {
                final cuentaActual = Provider.of<CuentaActual>(context, listen: false);
                final usuarioActual = Provider.of<Usuario?>(context, listen: false);

                double? importeValor = double.tryParse(importe.text);

                if (usuarioActual == null || cuentaActual.getCuentaActual() == null) {
                  return;
                }

                TipoMovimiento tipoMovimiento;

                if(groupValueTipo == 0) {
                  tipoMovimiento = TipoMovimiento.gasto;
                  importeValor = importeValor! * -1;
                }else{
                  tipoMovimiento = TipoMovimiento.ingreso;
                }

                TipoRecurrencia tipoRecurrencia = groupValueRecurrencia == 0 ? TipoRecurrencia.unico : TipoRecurrencia.recurrente;


                RecurrenciaMovimiento? recurrencia;
                if(groupValueRecurrencia == 0){
                  recurrencia = null;
                }else {
                  switch (recurrenciaSeleccionada) {
                    case 0:
                      recurrencia = RecurrenciaMovimiento.diario;
                      break;
                    case 1:
                      recurrencia = RecurrenciaMovimiento.semanal;
                      break;
                    case 2:
                      recurrencia = RecurrenciaMovimiento.mensual;
                      break;
                    case 3:
                      recurrencia = RecurrenciaMovimiento.anual;
                      break;
                  }
                }

                final Movimiento movimiento = Movimiento(tipoMovimiento: tipoMovimiento, tipoRecurrencia: tipoRecurrencia, importe: importeValor!, fecha: fechaSeleccionada,recurrencia: recurrencia, categoria: categoriaSeleccionada, uid: usuarioActual.getUid());

                await MovimientosRecurrentesManager.aniadirMovimiento(movimiento: movimiento, cuentaActual: cuentaActual);

                Navigator.pop(context);
              } : null,
              icon: const Icon(Icons.check)
          )
        ],
        title: Text(AppLocalizations.of(context)!.anadirMovimiento, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(vertical: 30.h,horizontal: 30.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LineaTexto(texto: AppLocalizations.of(context)!.tipoMovimientoEtiqueta),

            construirSelector(AppLocalizations.of(context)!.gastoSelector, AppLocalizations.of(context)!.ingresoSelector, groupValueTipo, (value){setState(() {groupValueTipo = value;});}),

            SizedBox(height: 25.h,),

            LineaTexto(texto: AppLocalizations.of(context)!.recurrenciaEtiqueta),

            construirSelector(AppLocalizations.of(context)!.unicoSelector, AppLocalizations.of(context)!.recurrenteSelector, groupValueRecurrencia, (value){setState(() {groupValueRecurrencia = value;});}),

            SizedBox(height: 25.h,),

            LineaTextfieldImporte(textController: importe,  comprobarError: (error){setState(() {estaDesabilitado = error;});}),

            SizedBox(height: 25.h,),

            Row(
              children: [
                Text(AppLocalizations.of(context)!.categoriaEtiqueta, style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600),),
                SizedBox(width: 5.w,),
                DropdownMenu<Categoria>(
                  initialSelection: categoriaSeleccionada,
                  leadingIcon: Icon(categoriaSeleccionada.icono, color: categoriaSeleccionada.colorIcono,),
                  onSelected: (Categoria? value) {
                    if (value != null) {
                      setState(() {
                        categoriaSeleccionada = value;
                      });
                    }
                  },
                  dropdownMenuEntries: Categoria.values.map((categoria) {
                    return DropdownMenuEntry<Categoria>(
                      value: categoria,
                      label: categoria.nombre(context),
                      leadingIcon: Icon(categoria.icono, color: categoria.colorIcono,)
                    );
                  }).toList(),
                )
              ],
            ),

            SizedBox(height: 25.h,),

            groupValueRecurrencia==1 ? LineaTexto(texto: AppLocalizations.of(context)!.seleccioneFechaInicio) : LineaTexto(texto: AppLocalizations.of(context)!.seleccioneFecha),

            Container(
              decoration: BoxDecoration(
                border: Border.all(width: 1),
              ),
              height: 40.h,
              child: InkWell(
                onTap: () {
                  _selectDate(context);
                },
                child:Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    const Icon(Icons.calendar_month),
                    Text(DateFormat.yMMMd().format(fechaSeleccionada)),
                    Icon(Icons.arrow_drop_down),
                  ],
                ),
              ),
            ),

            if(groupValueRecurrencia==1) ...[
              SizedBox(height: 15.h,),
              InkWell(
                onTap: (){

                },
                child:Text(AppLocalizations.of(context)!.anadirFechaFin, style: const TextStyle(color: Color(0xFF2563EB), decoration: TextDecoration.underline)),
              ),

              SizedBox(height: 25.h,),

              LineaTexto(texto: AppLocalizations.of(context)!.seleccioneRecurrencia),

              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    LineaChips(texto: AppLocalizations.of(context)!.diarioChip, indice: 0, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.semanalChip, indice: 1, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.mensualChip, indice: 2, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.anualChip, indice: 3, chipSeleccionado: recurrenciaSeleccionada, onChipSeleccionado: (indice) {setState(() {recurrenciaSeleccionada = indice;});},),
                  ],
                ),
              ),
            ]

          ],
        ),
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
            borderRadius: BorderRadius.circular(10),
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
          fontSize: 16.sp
        ),
      ),
    )
    );
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
        context: context,
        initialDate: fechaSeleccionada,
        firstDate: DateTime(minYear),
        lastDate: DateTime(maxYear));
    if (picked != null) {
      _onDateChange(picked);
    }
  }
}
