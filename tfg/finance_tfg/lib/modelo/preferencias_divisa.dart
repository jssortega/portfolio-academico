import 'package:flutter/cupertino.dart';
import 'currency_info.dart';
import 'currency_service.dart';

class PreferenciasDivisa extends ChangeNotifier {
  String _divisaActual = "EUR";
  Map<String, CurrencyInfo> _mapaDivisas = {};

  Map<String, double> _tasasCambio = {};

  String getdivisaActual() => _divisaActual;

  String getsimboloActual() {
    return _mapaDivisas[_divisaActual]?.symbol ?? "€";
  }

  void cambiarDivisa(String nuevaDivisa) {
    _divisaActual = nuevaDivisa;
    notifyListeners();
  }

  void setMapaDivisas(Map<String, CurrencyInfo> map){
    _mapaDivisas = map;
    notifyListeners();
  }

  Future<void> cargarTasas() async {
    try {
      final servicio = CurrencyService();
      _tasasCambio = await servicio.getCurrencyRate();
      notifyListeners();
    } catch (e) {
      print("Error al cargar las tasas de cambio: $e");
    }
  }

  double calcularImporte(double importeEuros) {
    if (_tasasCambio.isEmpty || _divisaActual == "EUR") {
      return importeEuros;
    }

    double tasaEuro = _tasasCambio["EUR"] ?? 1.0;
    double tasaImporteDeseado = _tasasCambio[_divisaActual] ?? 1.0;

    double importeCalculado = (importeEuros / tasaEuro) * tasaImporteDeseado;

    return importeCalculado;
  }
}