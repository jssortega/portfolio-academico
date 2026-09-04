import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/utils/global.dart';

class RegistrarsePantalla extends StatefulWidget {
  const RegistrarsePantalla({super.key});

  @override
  State<RegistrarsePantalla> createState() => _RegistrarsePantallaState();
}

class _RegistrarsePantallaState extends State<RegistrarsePantalla> {

  TextEditingController controllerNombre = TextEditingController();
  TextEditingController controllerNombreUsuario = TextEditingController();
  TextEditingController controllerEmail = TextEditingController();
  TextEditingController controllerContrasena = TextEditingController();
  TextEditingController controllerConfirmarContrasena = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Registrarse", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.only(left: 30.w, top: 15.h, right: 30.w, bottom: 20.h),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      LineaTexto(texto: "Nombre"),
                      LineaTextfield(textController: controllerNombre, prefixIcon: Icons.person, hintText: "Jesús", ),
                      SizedBox(height: 15.h,),
                      LineaTexto(texto: "Nombre de usuario"),
                      LineaTextfield(textController: controllerNombreUsuario, prefixIcon: Icons.perm_identity, hintText: "example_000", ),
                      SizedBox(height: 15.h,),
                      LineaTexto(texto: "Email"),
                      LineaTextfield(textController: controllerEmail, prefixIcon: Icons.mail, hintText: "example@gmail.com"),
                      SizedBox(height: 15.h,),
                      LineaTexto(texto: "Contraseña"),
                      LineaTextfieldContrasena(textController: controllerContrasena),
                      SizedBox(height: 15.h,),
                      LineaTexto(texto: "Confirmar contraseña"),
                      LineaTextfieldContrasena(textController: controllerConfirmarContrasena),
                    ],
                  ),
                ],
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.only(bottom: 30.h),
            child: Column(
              children: [
                BotonPrincipal(
                  texto: "Registrarse",
                  onPressed: () async {
                    if(controllerContrasena.text == controllerConfirmarContrasena.text){
                      Usuario usuario = Usuario(nombre: controllerNombre.text.trim(), nombreUsuario: controllerNombreUsuario.text.trim(), email: controllerEmail.text.trim());

                      await AccesoBBDD.instancia.registrarUsuario(usuario, controllerContrasena.text);
                    }
                  },
                ),
                SizedBox(height: 10.h,),
                InkWell(
                  onTap: (){
                    Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (context){
                              return IniciarSesionPantalla();
                            }
                        )
                    );
                  },
                  child: Text("¿Ya tiene cuenta? Iniciar sesión", style: TextStyle(color: Color(0xFF2563EB), decoration: TextDecoration.underline, fontSize: 16.sp)),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}
