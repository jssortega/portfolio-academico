import 'dart:io';

import 'package:finance_tfg/componentes/componentes.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

class EditarPerfilPantalla extends StatefulWidget {
  const EditarPerfilPantalla({super.key});

  @override
  State<EditarPerfilPantalla> createState() => _EditarPerfilPantallaState();
}

class _EditarPerfilPantallaState extends State<EditarPerfilPantalla> {
  late final TextEditingController controllerNombre;
  late final TextEditingController controllerNombreUsuario;
  late final TextEditingController controllerEmail;
  File? _imagenSeleccionada;

  bool _cargado = false;

  @override
  void initState() {
    super.initState();
    controllerNombre = TextEditingController();
    controllerNombreUsuario = TextEditingController();
    controllerEmail = TextEditingController();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    final usuarioActual = Provider.of<Usuario?>(context);

    if (!_cargado && usuarioActual != null) {
      controllerNombre.text = usuarioActual.getNombre();
      controllerNombreUsuario.text = usuarioActual.getNombreUsuario();
      controllerEmail.text = usuarioActual.getEmail();

      _cargado = true;
    }
  }

  @override
  void dispose() {
    controllerNombre.dispose();
    controllerNombreUsuario.dispose();
    controllerEmail.dispose();
    super.dispose();
  }

  Future<void> _seleccionarImagen() async {
    final ImagePicker picker = ImagePicker();

    final XFile? imagen = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 75,
    );

    if (imagen == null) return;

    setState(() {
      _imagenSeleccionada = File(imagen.path);
    });
  }

  Future<String?> _mostrarDialogoContrasena() async {
    final TextEditingController passwordController = TextEditingController();

    return showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title:  Text(AppLocalizations.of(context)!.confirmarCambioEmailTitulo),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
               Text(AppLocalizations.of(context)!.introduceContrasenaActual),
              SizedBox(height: 15.h),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration:  InputDecoration(
                  labelText: AppLocalizations.of(context)!.contrasenaCampo,
                  hintText: AppLocalizations.of(context)!.introduceContrasenaHint,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, null),
              child:  Text(AppLocalizations.of(context)!.cancelarBoton),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, passwordController.text.trim()),
              child:  Text(AppLocalizations.of(context)!.confirmarBoton),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final usuarioActual = Provider.of<Usuario?>(context);

    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: () async {
                final emailOriginal = usuarioActual?.getEmail() ?? "";
                final nuevoEmail = controllerEmail.text.trim();
                String? contrasena;

                if (nuevoEmail != emailOriginal) {
                  contrasena = await _mostrarDialogoContrasena();

                  if (contrasena == null || contrasena.isEmpty) {
                    return;
                  }
                }

                AccesoBBDD.instancia.actualizarUsuario(controllerNombre.text, controllerNombreUsuario.text, controllerEmail.text, _imagenSeleccionada, contrasena);
                Navigator.pop(context);
              },
              icon: const Icon(Icons.check)
          )
        ],
        title: Text(AppLocalizations.of(context)!.editarPerfilDrawer, style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 30.h,horizontal: 30.w),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Stack(
                        children: [
                          AvatarUsuario(
                            imagenPerfil: usuarioActual?.getImagenPerfil(),
                            imagenSeleccionada: _imagenSeleccionada,
                            radio: 52.r,
                            iconSize: 50.r,
                          ),
                          Positioned(
                            bottom: 0,
                            right: 0,
                            child: InkWell(
                              onTap: _seleccionarImagen,
                              borderRadius: BorderRadius.circular(50.r),
                              child: CircleAvatar(
                                radius: 18.r,
                                backgroundColor: Theme.of(context).primaryColor,
                                child: Icon(
                                  Icons.camera_alt,
                                  size: 18.r,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                        ]
                      ),
                    ],
                  ),
                  LineaTexto(texto: AppLocalizations.of(context)!.nombre),
                  SizedBox(height: 2.h,),
                  LineaTextfield(textController: controllerNombre, prefixIcon: Icons.person, hintText: usuarioActual?.getNombre(),),

                  SizedBox(height: 10.h,),

                  LineaTexto(texto: AppLocalizations.of(context)!.nombreUsuario),
                  SizedBox(height: 2.h,),
                  LineaTextfield(textController: controllerNombreUsuario, prefixIcon: Icons.perm_identity, hintText: usuarioActual?.getNombreUsuario(),),

                  SizedBox(height: 10.h,),

                  LineaTexto(texto: AppLocalizations.of(context)!.email),
                  SizedBox(height: 2.h,),
                  LineaTextfield(textController: controllerEmail, prefixIcon: Icons.mail, hintText: usuarioActual?.getEmail(),),

                  SizedBox(height: 10.h,),
                ],
              ),
              InkWell(
                onTap: () async {
                  final TextEditingController passwordController = TextEditingController();

                  final password = await showDialog<String>(
                    context: context,
                    builder: (context) {
                      return AlertDialog(
                        title:  Text(AppLocalizations.of(context)!.eliminarCuentaTituloPerfil),
                        content: TextField(
                          controller: passwordController,
                          obscureText: true,
                          decoration:  InputDecoration(
                            labelText: AppLocalizations.of(context)!.contrasenaCampo,
                            hintText: AppLocalizations.of(context)!.introduceContrasenaHint,
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () {
                              Navigator.pop(context);
                            },
                            child:  Text(AppLocalizations.of(context)!.cancelarBoton),
                          ),
                          TextButton(
                            onPressed: () {
                              Navigator.pop(context, passwordController.text.trim());
                            },
                            child:  Text(AppLocalizations.of(context)!.eliminarBoton, style: TextStyle(color: Colors.red),),
                          ),
                        ],
                      );
                    },
                  );

                  AccesoBBDD.instancia.eliminarUsuario(usuarioActual!.getUid(), password!);
                },
                child: Text(AppLocalizations.of(context)!.eliminarCuenta, style: TextStyle(color: Color(0xFFF15858), decoration: TextDecoration.underline, fontSize: 16.sp)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
