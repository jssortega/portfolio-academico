class CurrencyResponse {
  final Map<String, double> rates;

  const CurrencyResponse({required this.rates});
  factory CurrencyResponse.fromJson(Map<String, dynamic> json) {
    if (!json.containsKey('data') || json['data'] is! Map<String, dynamic>) {
      throw const FormatException('Invalid currency API response format.');
    }
    final Map<String, double> parsedData =
    (json['data'] as Map<String, dynamic>)
        .map((key, value) => MapEntry(key, (value as num).toDouble()));
    return CurrencyResponse(rates: parsedData);
  }
}