import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class LineaTextfieldImporte extends StatefulWidget {
  final bool textoArriba;
  final TextEditingController textController;
  final Function (bool) comprobarError;



  const LineaTextfieldImporte({super.key, required this.textController,this.textoArriba = false, required this.comprobarError});

  @override
  State<LineaTextfieldImporte> createState() => _LineaTextfieldImporteState();
}

class _LineaTextfieldImporteState extends State<LineaTextfieldImporte> {
  Error mensajeError = Error.estadoNull;
  
  @override
  Widget build(BuildContext context) {
    if(widget.textoArriba){
      return Row(
        children: [
          Expanded(
            child: construirTextField()
          ),
          const Icon(Icons.euro),
          SizedBox(width: 30.w,),
        ],
      );

    } else{
      return Row(
        children: [
          Text("Importe:", style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600),),
          SizedBox(width: 8.w,),
          Expanded(
            child: construirTextField()
          ),
          const Icon(Icons.euro),
        ],
      );
    }
  }

  Widget construirTextField(){
    return TextField(
      textAlign: TextAlign.start,
      keyboardType: const TextInputType.numberWithOptions(
          signed: true,
          decimal: true
      ),
      controller: widget.textController,
      decoration: InputDecoration(
          hintText: "0.00",
          hintStyle: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w500, color: Color(0xFF828FA2)),
          errorText: mensajeError.mensaje
      ),
      onChanged: (texto) {
        var parsedValue = double.tryParse(texto);

        final partes = texto.split('.');
        bool tieneMasDeDosDecimales = false;

        if (partes.length > 1) {
          tieneMasDeDosDecimales = partes[1].length > 2;
        }

        setState(() {
          if (texto.isEmpty) {
            mensajeError = Error.estadoNull;
            widget.comprobarError(false);
          } else if (parsedValue == null){
            mensajeError = Error.importeNoValido;
            widget.comprobarError(true);
          } else if(parsedValue.isNegative){
            mensajeError = Error.importeNegativo;
            widget.comprobarError(true);
          } else if(tieneMasDeDosDecimales){
            mensajeError = Error.importeDosDecimales;
            widget.comprobarError(true);
          } else{
            mensajeError = Error.estadoNull;
            widget.comprobarError(false);
          }
        });
      },
    );
  }
}
