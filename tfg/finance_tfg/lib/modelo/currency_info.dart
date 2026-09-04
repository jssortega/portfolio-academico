import 'dart:convert';
import 'package:flutter/services.dart';

class CurrencyInfo {
  String symbol;
  String flag;
  String currencyName;
  String countryName;
  double? rate;
  CurrencyInfo(
      {required this.symbol,
        required this.flag,
        required this.countryName,
        required this.currencyName,
        this.rate});
}
class ConvertJsonToMap {
  static Future<Map<String, CurrencyInfo>> readCurrenciesFromJson() async {
    try {
      final String response = await rootBundle.loadString('currency_info.json');
      final Map<String, dynamic> data = json.decode(response);
      final Map<String, CurrencyInfo> parsedData = data.map((key, value) =>
          MapEntry(
              key,
              CurrencyInfo(
                  symbol: value["symbol"],
                  flag: value["flag"],
                  countryName: value["country_name"],
                  currencyName: value["currency_name"])));
      return parsedData;
    } catch (e) {
      print("Error loading JSON: $e");
    }
    return <String, CurrencyInfo>{};
  }
}