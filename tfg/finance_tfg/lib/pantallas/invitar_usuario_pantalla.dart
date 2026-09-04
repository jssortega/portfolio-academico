import 'package:flutter/material.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';


class InvitarUsuarioPantalla extends StatefulWidget {
  const InvitarUsuarioPantalla({super.key});

  @override
  State<InvitarUsuarioPantalla> createState() => _InvitarUsuarioPantallaState();
}

class _InvitarUsuarioPantallaState extends State<InvitarUsuarioPantalla> {

  TextEditingController controllerNombreUsuario = TextEditingController();

  Rol seleccionado = Rol.administrador;

  List<Usuario> sugerencias = [];
  Usuario? usuarioSeleccionado;

  @override
  void dispose() {
    controllerNombreUsuario.dispose();
    super.dispose();
  }

  Future<void> buscarUsuarios(String texto) async {
    final textoLimpio = texto.trim().toLowerCase();

    if (textoLimpio.length < 2) {
      setState(() {
        sugerencias = [];
        usuarioSeleccionado = null;
      });
      return;
    }

    final resultados = await AccesoBBDD.instancia.buscarUsuariosPorNombre(textoLimpio);

    setState(() {
      sugerencias = resultados;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.invitarUsuarioTitulo, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: Padding(
        padding: EdgeInsets.fromLTRB(30.w, 30.h, 30.w, 60.h),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.start,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                LineaTexto(texto: AppLocalizations.of(context)!.nombreUsuarioCampo),

                Autocomplete<Usuario>(
                  displayStringForOption: (Usuario usuario) => usuario.getNombreUsuario(),
                  optionsBuilder: (TextEditingValue textEditingValue) {
                    if (textEditingValue.text.trim().length < 2) {
                      return const Iterable<Usuario>.empty();
                    }
                    return sugerencias;
                  },
                  onSelected: (Usuario usuario) {
                    usuarioSeleccionado = usuario;
                    controllerNombreUsuario.text = usuario.getNombreUsuario();
                  },
                  fieldViewBuilder: (context, textEditingController, focusNode, onFieldSubmitted,) {
                    textEditingController.text = controllerNombreUsuario.text;

                    return TextField(
                      controller: textEditingController,
                      focusNode: focusNode,
                      onChanged: (value) async {
                        controllerNombreUsuario.text = value;

                        if (usuarioSeleccionado != null && value.trim() != usuarioSeleccionado!.getNombreUsuario()) {
                          usuarioSeleccionado = null;
                        }

                        await buscarUsuarios(value);
                      },
                      decoration: InputDecoration(
                        hintText: AppLocalizations.of(context)!.ejemploNombreUsuario,
                        prefixIcon: const Icon(Icons.perm_identity),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12.r),),
                      ),
                    );
                  },
                  optionsViewBuilder: (context, onSelected, options,) {
                    return Align(
                      alignment: Alignment.topLeft,
                      child: Material(
                        elevation: 4,
                        borderRadius: BorderRadius.circular(12.r),
                        child: SizedBox(
                          width: 360.w,
                          child: ListView.builder(
                            padding: EdgeInsets.zero,
                            shrinkWrap: true,
                            itemCount: options.length,
                            itemBuilder: (context, index) {
                              final usuario = options.elementAt(index);

                              return ListTile(
                                leading: const Icon(Icons.person_outline),
                                title: Text(usuario.getNombreUsuario()),
                                onTap: () => onSelected(usuario),
                              );
                            },
                          ),
                        ),
                      ),
                    );
                  },

                ),

                SizedBox(height: 30.h,),

                LineaTexto(texto: AppLocalizations.of(context)!.seleccioneRol),

                Row(
                  children: [
                    Expanded(child: construirCard(Rol.administrador)),
                    Expanded(child: construirCard(Rol.consultor))
                  ],
                )
              ],
            ),
            BotonPrincipal(
              texto: AppLocalizations.of(context)!.invitarBoton,
              onPressed: () async {
                final usuarioActual = Provider.of<Usuario?>(context, listen: false);
                final cuentaActual = Provider.of<CuentaActual>(context, listen: false);

                if (usuarioActual == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                     SnackBar(content: Text(AppLocalizations.of(context)!.usuarioActualNoCargado)),
                  );
                  return;
                }

                if (cuentaActual.getCuentaActual() == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                     SnackBar(content: Text(AppLocalizations.of(context)!.sinCuentaSeleccionada)),
                  );
                  return;
                }

                if (usuarioSeleccionado == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                     SnackBar(content: Text(AppLocalizations.of(context)!.seleccionaUsuarioValido)),
                  );
                  return;
                }

                Invitacion invitacion = Invitacion(uidOrigen: usuarioActual.getUid(), uidDestino: usuarioSeleccionado!.getUid(), cuentaId: cuentaActual.getCuentaActual()!.cuenta.getId(), rolAsignado: seleccionado.name, estado: "Pendiente", nombreUsuarioOrigen: usuarioActual.getNombre(), nombreCuenta: cuentaActual.getCuentaActual()!.cuenta.getNombre(),);

                await AccesoBBDD.instancia.crearInvitacion(invitacion);
                },
            ),
          ],
        ),
      ),
    );
  }

  Widget construirCard(Rol rol){
    return Card(
      elevation: 5,
      color: rol == seleccionado ? Color(0xFFEFF2F4) : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12.r),
        side: BorderSide(
          color: rol == seleccionado ? Colors.black : Colors.transparent,
          width: 2,
        ),
      ),
      child: InkWell(
        onTap: (){
          setState(() {
            seleccionado = rol;
          });
        },
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 24.h,horizontal: 12.w),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(rol.icono),
              Text(rol.nombre(context), style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w500),),
              Text(rol.explicacion(context), style: TextStyle(color: Color(0xFF67778D),fontSize: 16.sp, fontWeight: FontWeight.w400),)
            ],
          ),
        ),
      ),
    );
  }
}
