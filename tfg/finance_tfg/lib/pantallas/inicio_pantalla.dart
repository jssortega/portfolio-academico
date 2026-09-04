import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

class InicioPantalla extends StatefulWidget {
  const InicioPantalla({super.key});

  @override
  State<InicioPantalla> createState() => _InicioPantallaState();
}

class _InicioPantallaState extends State<InicioPantalla> {

  int chipSeleccionado = 0;

  @override
  Widget build(BuildContext context) {
    final usuarioActual = Provider.of<Usuario?>(context);
    final cuentaActual = Provider.of<CuentaActual>(context);
    final esConsultor = cuentaActual.esConsultor();

    final listaMovimientos = Provider.of<List<Movimiento>?>(context);
    if(listaMovimientos == null){
      return CircularProgressIndicator();
    }
    final listaFiltrada = _filtrarMovimientos(listaMovimientos);
    final ultimosCuatro = listaFiltrada.take(4).toList();



    final preferenciasVisuales = Provider.of<PreferenciasVisuales>(context);

    return Scaffold(
      backgroundColor: Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Color(0xFFF8FAFC),
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.only(bottom: 110.h),
        child: Padding(
          padding: EdgeInsets.only(bottom: 30.h),
          child: Column(
            children: [

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () {
                      preferenciasVisuales.ocultarImportes();
                    },
                    icon: Icon(preferenciasVisuales.getOcultarImportes() ?  Icons.visibility : Icons.visibility_off, color: Color(0xFF828FA2), size: 24.sp,),
                    label: Text(preferenciasVisuales.getOcultarImportes() ?  AppLocalizations.of(context)!.mostrarSaldo : AppLocalizations.of(context)!.ocultarSaldo, style: TextStyle(color: Color(0xFF828FA2), fontSize: 24.sp, fontWeight: FontWeight.w500),),
                    style: ElevatedButton.styleFrom(backgroundColor: Color(0xFFF8FAFC), elevation: 0)
                  )
                ],
              ),

              const CardSaldoActual(),

              SizedBox(height: 15.h),

              Row(
                mainAxisAlignment: MainAxisAlignment.start,
                children: [
                  SizedBox(width: 32.w,),
                  Text(AppLocalizations.of(context)!.ultimosMovimientos, style: TextStyle(fontSize: 24.sp),),
                ],
              ),

              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    Icon(Icons.filter_alt, color: Color(0xFF828FA2), size: 32.sp,),
                    LineaChips(texto: AppLocalizations.of(context)!.todosChip, indice: 0, chipSeleccionado: chipSeleccionado, onChipSeleccionado: (indice) {setState(() {chipSeleccionado = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.fijosChip, indice: 1, chipSeleccionado: chipSeleccionado, onChipSeleccionado: (indice) {setState(() {chipSeleccionado = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.ingresosChip, indice: 2, chipSeleccionado: chipSeleccionado, onChipSeleccionado: (indice) {setState(() {chipSeleccionado = indice;});},),
                    LineaChips(texto: AppLocalizations.of(context)!.gastosChip, indice: 3, chipSeleccionado: chipSeleccionado, onChipSeleccionado: (indice) {setState(() {chipSeleccionado = indice;});},)
                  ],
                ),
              ),

              SizedBox(height: 10.h,),

              if (ultimosCuatro.isEmpty) ...[
                const Center(
                  child: Text("Todavía no tienes movimientos"),
                )
              ],

              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: ultimosCuatro.length,
                itemBuilder: (context, index) {
                  final movimiento = ultimosCuatro[index];

                  return LineaMovimiento(iconoCategoria: movimiento.getCategoria().icono, nombreCategoria: movimiento.getCategoria().nombre(context), fecha: DateFormat('dd/MM').format(movimiento.getFecha()), importe: movimiento.getImporte(), iconoCategoriaColor: movimiento.getCategoria().colorIcono, tipo: movimiento.getTipoMovimiento().name, tipoRecurrencia: movimiento.getTipoRecurrencia(),);

                },
              ),

              SizedBox(height: 4.h,),

              Padding(
                padding: EdgeInsets.symmetric(vertical: 2.h, horizontal: 32.w),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Color(0xFFF1F5F9), elevation: 5, padding: EdgeInsets.symmetric(vertical: 12.h)),
                        onPressed: (){
                          Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (context){
                                    return UltimosMovimientosPantalla();
                                  }
                              )
                          );
                        },
                        child: Text(AppLocalizations.of(context)!.mostrarMas, style: TextStyle(color: Color(0xFF536073), fontSize: 20.sp),)
                      )
                    ),
                  ],
                )
              ),
            ],
          ),
        ),
      ),

      drawer: Drawer(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 30.h,horizontal: 10.w),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      SizedBox(width: 12.w,),
                      AvatarUsuario(
                        imagenPerfil: usuarioActual?.getImagenPerfil(),
                        radio: 36.r,
                        iconSize: 34.r,
                      ),
                      SizedBox(width: 8.w,),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(usuarioActual?.getNombre() ?? "Cargando...", style: TextStyle(color: Colors.black, fontSize: 24.sp, fontWeight: FontWeight.w600),),
                          Text("@${usuarioActual?.getNombreUsuario() ?? ""}" , style: TextStyle(color: Color(0xFF67778D), fontSize: 20.sp, fontWeight: FontWeight.w500),)
                        ],
                      )
                    ],
                  ),
                  SizedBox(height: 15.h,),

                  BotonPrincipal(
                    texto: AppLocalizations.of(context)!.editarPerfilDrawer,
                    padding: 10.sp,
                    onPressed: (){
                      Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) {
                              return Provider<Usuario?>.value(
                                value: usuarioActual,
                                child: const EditarPerfilPantalla(),
                              );
                            },
                          )
                      );
                    },
                  ),

                  SizedBox(height: 25.h,),
                  construirLineaDrawer(AppLocalizations.of(context)!.cambiarCuentaDrawer, Icons.compare_arrows, CuentasPantalla(), usuarioActual),
                  construirLineaDrawer(AppLocalizations.of(context)!.editarCuenta, Icons.edit, EditarCuentaPantalla(), usuarioActual),
                  construirLineaDrawer(AppLocalizations.of(context)!.gestionarUsuarios, Icons.supervisor_account, GestionarUsuariosPantalla(), usuarioActual),
                  construirLineaDrawer(AppLocalizations.of(context)!.bandejaDeEntrada, Icons.mail, BandejaEntradaPantalla(), usuarioActual),
                  construirLineaDrawer(AppLocalizations.of(context)!.idiomaDivisa, Icons.public, IdiomaDivisaPantalla(), usuarioActual),
                ],
              ),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Color(0xFFFFF1F2), padding: EdgeInsets.symmetric(vertical: 10.h), side: BorderSide.none),
                        onPressed: (){
                          AccesoBBDD.instancia.cerrarSesion();
                        },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.exit_to_app, color: Color(0xFFF15858),size: 24.sp,),
                            SizedBox(width: 5.w,),
                            Text(AppLocalizations.of(context)!.cerrarSesion, style: TextStyle(color: Color(0xFFF15858), fontSize: 24.sp),),
                          ],
                        )
                    ),
                  ),
                ],
              ),
            ],
          ),
        )
      ),

      floatingActionButton:esConsultor
          ? null
          : FloatingActionButton(
            backgroundColor: Color(0xFF1E293B),
            shape: const CircleBorder(),
            onPressed: (){
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) {
                    return Provider<Usuario?>.value(
                      value: usuarioActual,
                      child: const AnadirMovimientoPantalla(),
                    );
                  },
                ),
              );
            },
            child: const Icon(Icons.add, color: Colors.white,),
          ),

    );
  }

  Widget construirLineaDrawer(String texto, IconData icono, Widget pantalla, Usuario? usuarioActual){
    return ListTile(
      titleTextStyle: TextStyle(color: Colors.black, fontSize: 20.sp, fontWeight: FontWeight.w500),
      title: Text(texto),
      leading: Icon(icono, size: 30.sp,),
      onTap: (){
        Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) {
                return Provider<Usuario?>.value(
                  value: usuarioActual,
                  child: pantalla,
                );
              },
            )
        );
      }
    );
  }

  List<Movimiento> _filtrarMovimientos(List<Movimiento> movimientos) {
    switch (chipSeleccionado) {
      case 1:
        return movimientos.where((m) => m.getTipoRecurrencia() != TipoRecurrencia.unico).toList();

      case 2:
        return movimientos.where((m) => m.getTipoMovimiento() == TipoMovimiento.ingreso).toList();

      case 3:
        return movimientos.where((m) => m.getTipoMovimiento() == TipoMovimiento.gasto).toList();

      case 0:
      default:
        return movimientos;
    }
  }

}
