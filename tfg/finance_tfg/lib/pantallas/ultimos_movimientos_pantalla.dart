import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/componentes/linea_movimiento_detallado.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:intl/intl.dart';


class UltimosMovimientosPantalla extends StatelessWidget {
  const UltimosMovimientosPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    final listaMovimientos = Provider.of<List<Movimiento>?>(context);
    if(listaMovimientos == null){
      return CircularProgressIndicator();
    }

    final Map<String, double> balancePorDia = {};

    for (final movimiento in listaMovimientos) {
      final fecha = DateFormat('yyyy-MM-dd').format(movimiento.getFecha());
      balancePorDia[fecha] = (balancePorDia[fecha] ?? 0) + movimiento.getImporte();
    }

    return Scaffold(
      appBar: AppBar(
        title: Text("Últimos movimientos", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 20.w),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              CardSaldoActual(),

              SizedBox(height: 30.h,),

              if(listaMovimientos.isEmpty) ...[
                const Center(
                child: Text("Todavía no tienes movimientos"),
                )
              ]else...[

                FutureBuilder<Map<String, Usuario>>(
                  future: obtenerUsuariosDeMovimientos(listaMovimientos),
                  builder: (context, snapshot) {

                    if (!snapshot.hasData) {
                      return const Center(
                        child: CircularProgressIndicator(),
                      );
                    }

                    final usuarios = snapshot.data!;

                    return ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: listaMovimientos.length,
                      itemBuilder: (context, index){
                        final movimiento = listaMovimientos[index];
                        final fechaActual = DateFormat('yyyy-MM-dd').format(movimiento.getFecha());

                        bool mostrarFecha;

                        if (index == 0) {
                          mostrarFecha = true;
                        } else {
                          final fechaActual = movimiento.getFecha();
                          final fechaAnterior = listaMovimientos[index - 1].getFecha();

                          mostrarFecha = !DateUtils.isSameDay(fechaActual, fechaAnterior,);
                        }

                        return LineaMovimientoDetallado(movimiento: movimiento, mostrarFecha: mostrarFecha, balance: balancePorDia[fechaActual] ?? 0, usuario: usuarios[movimiento.getUidUsuario()],);
                      }
                    );
                  }
                )
              ],
            ],
          ),
        ),
      ),
    );
  }

  Future<Map<String,Usuario>> obtenerUsuariosDeMovimientos(List<Movimiento> listaMovimientos) async{
    final Map<String, Usuario> usuarios = {};
    final List<String> uidsDistintos = [];

    for(Movimiento movimiento in listaMovimientos){
      if(!uidsDistintos.contains(movimiento.getUidUsuario())){
        uidsDistintos.add(movimiento.getUidUsuario());
      }
    }

    for(String uid in uidsDistintos){
      usuarios[uid] = await AccesoBBDD.instancia.buscarUsuarioPorUid(uid) as Usuario;
    }

    return usuarios;
  }
}
