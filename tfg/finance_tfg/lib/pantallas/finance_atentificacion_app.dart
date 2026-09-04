import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class FinanceAtentificacionApp extends StatelessWidget {
  const FinanceAtentificacionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        }

        if (!snapshot.hasData) {
          return const IniciarSesionPantalla();
        }

        return StreamProvider<Usuario?>.value(
          value: AccesoBBDD.instancia.getUsuarioActual(),
          initialData: null,
          child: const FinanceCuentaApp(),
        );
      },
    );
  }
}