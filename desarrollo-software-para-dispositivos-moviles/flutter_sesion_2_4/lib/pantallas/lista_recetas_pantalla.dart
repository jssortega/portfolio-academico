import 'package:flutter/material.dart';
import 'package:flutter_sesion_2_4/modelo/modelo.dart';
import 'package:flutter_sesion_2_4/componentes/componentes.dart';

class ListaRecetasPantalla extends StatelessWidget {
  const ListaRecetasPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
              future: ServicioRecetasHttp.getRecetas(),
              builder: (context, AsyncSnapshot snapshot) {
                if (snapshot.connectionState == ConnectionState.done) {
                  if (snapshot.hasError) {
                    return const Center(
                      child: Text('No se puede conectar con el servidor'),
                    );
                  } else {
                    if((snapshot.data as List<RecetaBasica>).isNotEmpty){
                      return GridRecetas(recetas: snapshot.data,);
                    }else{
                      return const Center(
                          child: Text("No se ha encontrado recetas con ese criterio")
                      );
                    }
                  }
                } else {
                  return const Center(child: CircularProgressIndicator(),);
                }
              },
            );
  }
}
