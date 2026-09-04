import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';

class CuentasPantalla extends StatelessWidget {
  const CuentasPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: (){
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context){
                          return BandejaEntradaPantalla();
                        }
                    )
                );
              },
              icon: const Icon(Icons.notifications)
          )
        ],
        title: Text(AppLocalizations.of(context)!.cuentasTitulo, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 30.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: StreamBuilder<List<CuentaConRol>>(
                stream: AccesoBBDD.instancia.getCuentasUsuario(),
                builder: (context, snapshot) {
                  if(snapshot.connectionState == ConnectionState.waiting){
                    return const Center(
                      child: CircularProgressIndicator(),
                    );
                  }

                  if(snapshot.hasError){
                    return Center(
                      child: Text(AppLocalizations.of(context)!.errorCargarCuentas),
                    );
                  }

                  final listaCuentas = snapshot.data ?? [];

                  if(listaCuentas.isEmpty){
                    return Center(
                      child: Text(AppLocalizations.of(context)!.sinCuentas),
                    );
                  }

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: EdgeInsets.only(bottom: 4.h),
                        child: Text(AppLocalizations.of(context)!.seleccioneCuenta, style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600),),
                        ),
                      Expanded(
                        child: ListView.builder(
                          itemCount: listaCuentas.length,
                          itemBuilder: (context, index){
                            return construirCardCuenta(context, listaCuentas[index]);
                          }
                        ),
                      )
                    ],
                  );
                }
              ),
            ),
            SizedBox(height: 20.h,),
            BotonPrincipal(
              texto: AppLocalizations.of(context)!.crearCuentaButtom,
              onPressed: (){
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context){
                          return AniadirCuentaPantalla();
                        }
                    )
                );
              },
            ),
          ],
        ),
      )
    );
  }

  Widget construirCardCuenta(BuildContext context, CuentaConRol cuenta){
    final cuentaActual = Provider.of<CuentaActual>(context, listen: false);
    final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context);

    return Padding(
      padding: EdgeInsets.only(bottom: 5.h),
          child: InkWell(
            onTap: (){
              cuentaActual.seleccionarCuenta(cuenta);
              if (Navigator.canPop(context)) {
                Navigator.pop(context);
              }
            },
            child: Card(
              color: const Color(0xFFFFFFFF),
              elevation: 5,
              child: Padding(
                  padding: EdgeInsets.only(top: 20.h,bottom: 20.h,left: 15.w),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(cuenta.cuenta.getNombre(), style: TextStyle(color: Colors.black, fontSize: 24.sp ,fontWeight: FontWeight.w700),),
                          Text(cuenta.rol.nombre(context), style: TextStyle(color: Color(0xFF67778D), fontSize: 16.sp ,fontWeight: FontWeight.w600),),
                        ],
                      ),
                      Row(
                        children: [
                          Text(formatearImporte(preferenciasDivisa.calcularImporte(cuenta.cuenta.getSaldo())), style: TextStyle(color: Colors.black, fontSize: 32.sp ,fontWeight: FontWeight.bold),),
                          Text(preferenciasDivisa.getsimboloActual(), style: TextStyle(fontSize: 32.sp, fontWeight: FontWeight.w600))
                        ],
                      ),
                      PopupMenuButton(
                        iconSize: 42.sp,
                        onSelected: (String result) {

                        },
                        itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                          PopupMenuItem<String>(
                            value: 'Eliminar',
                            child:  Row(
                              children: [
                                Icon(Icons.delete),
                                Text(AppLocalizations.of(context)!.eliminarCuentaMenu)
                              ],
                            ),
                            onTap: (){
                              showDialog(
                                context: context,
                                barrierDismissible: false,
                                builder: (BuildContext context) {
                                  return AlertDialog(
                                    title:  Row(
                                      children: [
                                        Icon(Icons.warning_amber_rounded, color: Colors.amber, size: 30),
                                        SizedBox(width: 10),
                                        Text(AppLocalizations.of(context)!.eliminarCuentaTitulo),
                                      ],
                                    ),
                                    content:Text(AppLocalizations.of(context)!.confirmarEliminarCuenta),
                                    actions: <Widget>[
                                      TextButton(
                                        child: Text(AppLocalizations.of(context)!.cancelarEliminarCuenta, style: TextStyle(color: Colors.black)),
                                        onPressed: () {
                                          Navigator.of(context).pop();
                                        },
                                      ),
                                      TextButton(
                                        child: Text(AppLocalizations.of(context)!.aceptarEliminarCuenta, style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                                        onPressed: () {
                                          AccesoBBDD.instancia.eliminarCuenta(cuenta.cuenta.getId());
                                          Navigator.of(context).pop();
                                        },
                                      ),
                                    ],
                                  );
                                },
                              );

                            },
                          ),
                        ],
                      )
                    ],
                  )
              )
            ),
          )
    );
  }
}
