import 'package:flutter/material.dart';

class ConversorPaginaPrincipal extends StatefulWidget {
  const ConversorPaginaPrincipal({super.key});

  @override
  State<ConversorPaginaPrincipal> createState() => _ConversorPaginaPrincipalState();
}


class _ConversorPaginaPrincipalState extends State<ConversorPaginaPrincipal> {
  late double _valorAConvertir;
  final _conversiones = ['Kilómetros a metros', 'Metros a kilómetros','Metros a centimetros'];
  late int _idConversionActual;
  late double _valorConvertido;
  @override
  void initState() {
    _valorAConvertir = 0.0;
    _idConversionActual = 0;
    _valorConvertido=0.0;

    super.initState();
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Conversor de unidades'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),

      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Text(
                    'Valor a convertir',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  TextField(
                    textAlign: TextAlign.center,
                    keyboardType: const TextInputType.numberWithOptions(
                        signed: true,
                        decimal: true
                    ),
                    onChanged: (texto) {
                      var valorIntroducido = double.tryParse(texto);
                      setState(() { _valorAConvertir = valorIntroducido ?? 0.0; });
                      _convertir();
                    },
                  ),
                  const SizedBox(
                    height: 32.0,
                  ),
                  Text(
                    'Convertir de',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  DropdownButton<String>(
                    value: _conversiones[_idConversionActual],
                    items: _conversiones.map((String value) {
                      return DropdownMenuItem<String>(
                        value: value,
                        child: Text(value),
                      );
                    }).toList(),
                    onChanged: (nuevoValor) {
                      setState(() {
                        _idConversionActual = _conversiones.indexOf(nuevoValor!);
                      });
                    },
                  ),
                  const SizedBox(
                    height: 32.0,
                  ),
                  Text(
                    'Resultado',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(
                    height: 16.0,
                  ),
                  Text(
                    '$_valorConvertido',
                    style: Theme.of(context).textTheme.headlineLarge,
                  ),
                  const SizedBox(
                    height: 32.0,
                  ),
                  /*ElevatedButton(
                    child: const Text(
                      'Convertir',
                    ),
                    onPressed: () {
                      _convertir();
                    },
                  ),*/
                ],
              ),
            ),
          ),
        ),
      ),
    );;
  }

  void _convertir() {
    double constanteConversion = 1.0;
    switch(_idConversionActual) {
      case 0: // Kilómetros a metros
        constanteConversion = 1000.0;
        break;
      case 1: // Metros a kilómetros
        constanteConversion = 0.001;
        break;
      case 2: //Metros a centimetros
        constanteConversion = 100;
        break;
      default:
        break;
    }
    setState(() {
      _valorConvertido = _valorAConvertir * constanteConversion;
    });
  }
}
