import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class GestionarUsuariosPantalla extends StatelessWidget {
  const GestionarUsuariosPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    final cuentaActual = Provider.of<CuentaActual>(context);
    final esAdministrador = cuentaActual.esAdministrador();
    final usuarioActual = Provider.of<Usuario?>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.gestionarUsuarios, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 32.h, horizontal: 32.w),
                child: StreamBuilder<List<UsuarioConRol>>(
                    stream: AccesoBBDD.instancia.getUsuariosCuentas(cuentaActual.getCuentaActual()!.cuenta.getId()),
                    builder: (context, snapshot) {
                      if(snapshot.connectionState == ConnectionState.waiting){
                        return const Center(
                          child: CircularProgressIndicator(),
                        );
                      }

                      if(snapshot.hasError){
                        return const Center(
                          child: Text("Error al cargar los usuarios"),
                        );
                      }

                      final listaUsuarios = snapshot.data ?? [];

                      if(listaUsuarios.isEmpty){
                        return const Center(
                          child: Text("Esta cuenta no tiene usuarios"),
                        );
                      }

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: EdgeInsets.only(bottom: 4.h),
                            child: LineaTexto(texto: AppLocalizations.of(context)!.usuarios)
                          ),
                          Expanded(
                            child: ListView.builder(
                                itemCount: listaUsuarios.length,
                                itemBuilder: (context, index){
                                  return construirCardUsuario(listaUsuarios[index].usuario.getNombre(), listaUsuarios[index].usuario.getNombreUsuario(),listaUsuarios[index].rol, cuentaActual.getCuentaActual()!.cuenta.getId(), listaUsuarios[index].usuario.getUid(), listaUsuarios[index].usuario.getImagenPerfil(), esAdministrador, context);
                                }
                            ),
                          )
                        ],
                      );
                    }
                ),
              ),
            ),
            SizedBox(height: 20.h,),
            if(esAdministrador)
              Padding(
                padding: EdgeInsets.symmetric(vertical: 32.h, horizontal: 32.w),
                child: OutlinedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF1E293B), padding: EdgeInsets.symmetric(vertical: 20.h)),
                    onPressed: (){
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) {
                            return Provider<Usuario?>.value(
                              value: usuarioActual,
                              child: const InvitarUsuarioPantalla(),
                            );
                          },
                        ),
                      );
                    },
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.person_add, color: Colors.white, size: 24.sp,),
                        SizedBox(width: 5.w,),
                        Text(AppLocalizations.of(context)!.aniadirUsuarioButtom, style: TextStyle(color: Colors.white, fontSize: 20.sp),),
                      ],
                    )
                ),
              )
          ],
        ),
      )
    );
  }

  Widget construirCardUsuario(String nombre, String nombreUsuario, String rol, String idCuenta, String uid, String imagenUsuario, bool esAdministrador, BuildContext context){
    return Padding(
        padding: EdgeInsets.only(bottom: 5.h),
        child: Card(
            color: const Color(0xFFFFFFFF),
            elevation: 5,
            child: Padding(
                padding: EdgeInsets.symmetric(vertical: 20.h,horizontal: 20.w),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.start,
                      children: [
                        AvatarUsuario(
                          imagenPerfil: imagenUsuario,
                          radio: 36.r,
                          iconSize: 34.r,
                        ),
                        SizedBox(width: 5.w,),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(nombre, style: TextStyle(color: Colors.black, fontSize: 24.sp ,fontWeight: FontWeight.w700),),
                            Text("@$nombreUsuario", style: TextStyle(color: Color(0xFF67778D), fontSize: 16.sp ,fontWeight: FontWeight.w600),),
                          ],
                        ),
                      ],
                    ),
                    esAdministrador ?
                    PopupMenuButton<String>(
                        padding: EdgeInsets.zero,
                        onSelected: (String nuevoRol) {
                          AccesoBBDD.instancia.actualizarRol(idCuenta, uid, nuevoRol);
                        },
                        itemBuilder: (BuildContext context) => [
                          PopupMenuItem<String>(
                            value: Rol.administrador.name,
                            child: Text(Rol.administrador.nombre(context)),
                          ),
                          PopupMenuItem<String>(
                            value: Rol.consultor.name,
                            child: Text(Rol.consultor.nombre(context)),
                          ),
                        ],
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              rol == 'administrador' ? Rol.administrador.nombre(context) : Rol.consultor.nombre(context),
                              style: TextStyle(
                                color: Colors.blue,
                                fontSize: 18.sp,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                            Icon(
                              Icons.arrow_drop_down,
                              color: Colors.blue,
                              size: 20.sp,
                            ),
                          ],
                        ),
                      )
                    : Text(rol == 'administrador' ? Rol.administrador.nombre(context) : Rol.consultor.nombre(context), style: TextStyle(color: const Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w600 ),),
                  ],
                )
            )
        )
    );
  }
}
