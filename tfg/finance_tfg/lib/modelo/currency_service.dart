import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'currency_response.dart';
import 'package:http/http.dart' as http;

class CurrencyService {
  static final String url = 'https://api.freecurrencyapi.com/v1/latest';
  final String _apiKey = dotenv.env['FREECURRENCY_API_KEY'] ?? '';


  Future<Map<String, double>> getCurrencyRate() async {
    if (_apiKey.isEmpty) {
      throw Exception('API key is missing. Please configure the API key.');
    }
    try {
      final response = await http.get(Uri.parse("$url?apikey=$_apiKey"));
      if (response.statusCode == 200) {
        final Map<String, dynamic> decodedJson = jsonDecode(response.body);
        if (!decodedJson.containsKey('data')) {
          throw const FormatException('Invalid API response');
        }
        final CurrencyResponse data = CurrencyResponse.fromJson(decodedJson);
        return data.rates;
      }
    } catch (e) {
      print("Exception: $e");
    }
    return {};
  }
}