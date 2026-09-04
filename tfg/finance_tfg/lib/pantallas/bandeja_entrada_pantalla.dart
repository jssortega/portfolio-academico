import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class BandejaEntradaPantalla extends StatelessWidget {
  const BandejaEntradaPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    final usuarioActual = Provider.of<Usuario?>(context);

    if(usuarioActual == null){
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text("Bandeja de entrada", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 30.h,horizontal: 20.w),
          child: StreamBuilder<List<Invitacion>>(
              stream: AccesoBBDD.instancia.getInvitacionesPendientes(usuarioActual.getUid()),
              builder: (context, snapshot) {

                if(snapshot.connectionState == ConnectionState.waiting){
                  return const Center(
                    child: CircularProgressIndicator(),
                  );
                }

                if (snapshot.hasError) {
                  return Center(
                    child: Text(AppLocalizations.of(context)!.errorConDetalle(snapshot.error.toString())),
                  );
                }

                final listaInvitaciones = snapshot.data ?? [];

                if(listaInvitaciones.isEmpty){
                  return Center(
                    child: Text(AppLocalizations.of(context)!.sinInvitacionesPendientes),
                  );
                }

                return ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: listaInvitaciones.length,
                    itemBuilder: (context, index){
                      final invitacion = listaInvitaciones[index];

                      return construirCard(invitacion, context);
                    }
                );

              }
          ),
        ),
      )
    );
  }

  Widget construirCard(Invitacion invitacion, BuildContext context){
    return Padding(
        padding: EdgeInsets.only(bottom: 5.h),
        child: Card(
            color: const  Color(0xFFFFFFFF),
            elevation: 5,
            child: Padding(
              padding: EdgeInsets.symmetric(vertical: 20.h,horizontal: 30.w),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        children: [
                          CircleAvatar(
                            backgroundColor: Colors.black,
                            radius: 28.r,
                          ),
                          Text(invitacion.getNombreUsuarioOrigen(), style: TextStyle(color: Colors.black, fontSize: 20.sp, fontWeight: FontWeight.w500),)
                        ],
                      ),
                      Column(
                        children: [
                          Text(AppLocalizations.of(context)!.invitacionCuentaTexto, style: TextStyle(color: Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w400),),
                          SizedBox(height: 2.h,),
                          Text(invitacion.getNombreCuenta(), style: TextStyle(color: Colors.black, fontSize: 24.sp, fontWeight: FontWeight.w600),),
                          SizedBox(height: 3.h,),
                          Row(
                            children: [
                              Text(AppLocalizations.of(context)!.conRolEtiqueta, style: TextStyle(color: Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w400),),
                              Text(invitacion.getRolAsignado(), style: TextStyle(color: Colors.black, fontSize: 20.sp, fontWeight: FontWeight.w500),)
                            ],
                          )
                        ],
                      )
                    ],
                  ),
                  SizedBox(height: 6.h,),
                  Row(
                    children: [
                      construirBoton(AppLocalizations.of(context)!.aceptarInvitacion, Color(0xFF24BF8B), true, invitacion.getId()),
                      SizedBox(width: 4.w,),
                      construirBoton(AppLocalizations.of(context)!.rechazarInvitacion, Color(0xFFF15858), false, invitacion.getId())
                    ],
                  )
                ],
              ),
            )
        )
    );
  }

  Widget construirBoton(String texto, Color color, bool botonAceptar, invitacionId){
    return Expanded(
      child: OutlinedButton(
          style: ElevatedButton.styleFrom(backgroundColor: color, padding: EdgeInsets.symmetric(vertical: 15.h), side: BorderSide.none),
          onPressed: (){
            botonAceptar ? AccesoBBDD.instancia.aceptarInvitacion(invitacionId) : AccesoBBDD.instancia.rechazarInvitacion(invitacionId);
          },
          child: Text(texto, style: TextStyle(color: Colors.white, fontSize: 20.sp),)
      ),
    );
  }
}
