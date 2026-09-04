import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class AniadirCuentaPantalla extends StatefulWidget {
  const AniadirCuentaPantalla({super.key});

  @override
  State<AniadirCuentaPantalla> createState() => _AniadirCuentaPantallaState();
}

class _AniadirCuentaPantallaState extends State<AniadirCuentaPantalla> {

  bool estaDesabilitado = false;

  final TextEditingController controllerNombre = TextEditingController();
  final TextEditingController controllerSaldo = TextEditingController();

  @override
  void dispose() {
    controllerNombre.dispose();
    controllerSaldo.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: !estaDesabilitado ? (){
                final String nombre = controllerNombre.text.trim();
                final double saldo = double.tryParse(controllerSaldo.text) ?? 0.0;

                Cuenta cuenta = Cuenta(nombre: nombre, saldo: saldo);
                AccesoBBDD.instancia.anadirCuenta(cuenta);
                Navigator.pop(context);
              } : null,
              icon: const Icon(Icons.check)
          )
        ],
        title: Text(AppLocalizations.of(context)!.anadirCuenta, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 30.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LineaTexto(texto: AppLocalizations.of(context)!.nombreCuenta),
            LineaTextfield(textController: controllerNombre, prefixIcon: Icons.account_balance, hintText: AppLocalizations.of(context)!.ejemploNombreCuentaTrabajo,),

            SizedBox(height: 16.h,),

            LineaTexto(texto: AppLocalizations.of(context)!.saldoInicial),
            LineaTextfieldImporte(textController: controllerSaldo, textoArriba: true, comprobarError: (error){setState(() {estaDesabilitado = error;});})
          ],
        ),
      ),
    );
  }
}
