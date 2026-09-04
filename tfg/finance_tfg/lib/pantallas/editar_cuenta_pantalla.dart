import 'package:flutter/material.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:provider/provider.dart';

class EditarCuentaPantalla extends StatefulWidget {
  const EditarCuentaPantalla({super.key});

  @override
  State<EditarCuentaPantalla> createState() => _EditarCuentaPantallaState();
}

class _EditarCuentaPantallaState extends State<EditarCuentaPantalla> {

  bool estaDesabilitado = false;

  late final TextEditingController controllerNombre;
  late final TextEditingController controllerSaldo;


  @override
  void initState() {
    super.initState();
    controllerNombre = TextEditingController();
    controllerSaldo = TextEditingController();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    final cuentaActual = Provider.of<CuentaActual>(context);

    controllerNombre.text = cuentaActual.getCuentaActual()!.cuenta.getNombre();
    controllerSaldo.text = cuentaActual.getCuentaActual()!.cuenta.getSaldo().toString();
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: !estaDesabilitado ? (){
                final cuentaActual = Provider.of<CuentaActual>(context, listen: false);
                final String nombre = controllerNombre.text.trim();
                final double saldo = double.tryParse(controllerSaldo.text) ?? 0.0;

                cuentaActual.editarCuenta(nombre, saldo);
                Navigator.pop(context);
              } : null,
              icon: const Icon(Icons.check)
          )
        ],
        title: Text(AppLocalizations.of(context)!.editarCuenta, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
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
