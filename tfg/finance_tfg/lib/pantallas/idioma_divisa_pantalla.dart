import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'package:finance_tfg/componentes/componentes.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:provider/provider.dart';

class IdiomaDivisaPantalla extends StatefulWidget {
  const IdiomaDivisaPantalla({super.key});

  @override
  State<IdiomaDivisaPantalla> createState() => _IdiomaDivisaPantallaState();
}

class _IdiomaDivisaPantallaState extends State<IdiomaDivisaPantalla> {

  late Idioma idiomaSeleccionado;
  late String divisaSeleccionada;

  late Future<Map<String, CurrencyInfo>> _divisasFuture;

  @override
  void initState(){
    super.initState();

    final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context, listen: false);
    divisaSeleccionada = preferenciasDivisa.getdivisaActual();

    _divisasFuture = ConvertJsonToMap.readCurrenciesFromJson();

    final localeActual = Provider.of<PreferenciasIdioma>(context,listen: false);

    if(localeActual.getIdiomaActual() == Locale('en')){
      idiomaSeleccionado = Idioma.ingles;
    } else{
      idiomaSeleccionado = Idioma.espaniol;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: () async {
                final preferenciasIdioma = Provider.of<PreferenciasIdioma>(context,listen: false);
                final preferenciasDivisa = Provider.of<PreferenciasDivisa>(context,listen: false);

                switch(idiomaSeleccionado){
                  case Idioma.espaniol:
                    preferenciasIdioma.cambiarIdioma(const Locale('es'));
                    break;
                  case Idioma.ingles:
                    preferenciasIdioma.cambiarIdioma(const Locale('en'));
                    break;
                }

                preferenciasDivisa.cambiarDivisa(divisaSeleccionada);
                preferenciasDivisa.setMapaDivisas(await _divisasFuture);


                Navigator.pop(context);
              },
              icon: const Icon(Icons.check)
          )
        ],
        title: Text("Idioma y divisa", style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w700),),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(vertical: 30.h, horizontal: 30.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LineaTexto(texto: "Seleccione idioma"),

            Container(
              width: double.infinity,
              height: 50.h,
              padding: EdgeInsets.symmetric(horizontal: 16.w),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<Idioma>(
                  value: idiomaSeleccionado,
                  isExpanded: true,
                  icon: const Icon(Icons.keyboard_arrow_down),
                  items: Idioma.values.map((idioma) {
                    return DropdownMenuItem<Idioma>(
                      value: idioma,
                      child: Row(
                        children: [
                          SizedBox(
                            width: 32.w,
                            child: Text(idioma.bandera, textAlign: TextAlign.center, style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600)),
                          ),
                          SizedBox(width: 16.w),
                          Text(idioma.nombre, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w600),),
                        ],
                      ),
                    );
                  }).toList(),
                  onChanged: (Idioma? value) {
                    if (value != null) {
                      setState(() {
                        idiomaSeleccionado = value;
                      });
                    }
                  },
                ),
              ),
            ),

            SizedBox(height: 20.h,),

            LineaTexto(texto: "Seleccione divisa"),
            FutureBuilder(
                future: _divisasFuture,
                builder: (context, snapshot){
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snapshot.hasError || !snapshot.hasData) {
                    return Center(child: Text("Error al obtener las divisas"));
                  }

                  final mapaDivisas = snapshot.data!;

                  return Container(
                    width: double.infinity,
                    height: 50.h,
                    padding: EdgeInsets.symmetric(horizontal: 16.w),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8.r),
                      border: Border.all(color: Colors.grey.shade300,),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: divisaSeleccionada,
                        isExpanded: true,
                        icon: const Icon(Icons.keyboard_arrow_down),
                        items: mapaDivisas.entries.map((divisa) {
                          final String sigla = divisa.key;
                          final CurrencyInfo info = divisa.value;
                          return DropdownMenuItem<String>(
                            value: sigla,
                            child: Row(
                              children: [
                                SizedBox(
                                  width: 32.w,
                                  child: Text(info.symbol, textAlign: TextAlign.center, style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.w600)),
                                ),
                                SizedBox(width: 16.w),
                                Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(info.currencyName, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w600, color: Colors.black,),),
                                    Text("${info.flag} - ${info.symbol}", style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w500, color: Color(0xFF828FA2)),),
                                  ],
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                        onChanged: (String? value) {
                          if (value != null) {
                            setState(() {
                              divisaSeleccionada = value;
                            });
                          }
                        },
                      ),
                    ),
                  );
                }
            )

          ],
        ),
      ),
    );
  }
}
