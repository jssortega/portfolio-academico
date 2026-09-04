import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/acceso_BBDD.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/utils/global.dart';

class IniciarSesionPantalla extends StatefulWidget {
  const IniciarSesionPantalla({super.key});

  @override
  State<IniciarSesionPantalla> createState() => _IniciarSesionPantallaState();
}

class _IniciarSesionPantallaState extends State<IniciarSesionPantalla> {

  TextEditingController controllerEmail = TextEditingController();
  TextEditingController controllerContrasena = TextEditingController();

  @override
  void dispose() {
    controllerEmail.dispose();
    controllerContrasena.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.only(left: 30.w, top: 150.h, right: 30.w, bottom: 50.h),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text("Iniciar sesión", style: TextStyle(fontSize: 36.sp, fontWeight: FontWeight.w700),)
                        ],
                      ),
                      SizedBox(height: 20.h,),
                      LineaTexto(texto: "Email"),
                      LineaTextfield(textController: controllerEmail, prefixIcon: Icons.mail, hintText: "example@gmail.com", ),
                      SizedBox(height: 15.h,),
                      LineaTexto(texto: "Contraseña"),
                      LineaTextfieldContrasena(textController: controllerContrasena),
                      SizedBox(height: 15.h,),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          InkWell(
                            onTap: (){

                            },
                            child: Text("¿Contraseña olvidada?", style: TextStyle(color: Color(0xFF2563EB), decoration: TextDecoration.underline, fontSize: 16.sp)),
                          ),
                        ],
                      ),
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
                  texto: "Iniciar sesión",
                  onPressed: () async {
                    await AccesoBBDD.instancia.inicioSesion(controllerEmail.text, controllerContrasena.text);
                  },
                ),
                SizedBox(height: 10.h,),
                InkWell(
                  onTap: (){
                    Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (context){
                              return RegistrarsePantalla();
                            }
                        )
                    );
                  },
                  child: Text("¿No tiene cuenta? Registrarse", style: TextStyle(color: Color(0xFF2563EB), decoration: TextDecoration.underline, fontSize: 16.sp)),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}
