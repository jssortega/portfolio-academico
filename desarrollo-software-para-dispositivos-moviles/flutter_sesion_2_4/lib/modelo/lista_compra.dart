import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'producto.dart';
import 'package:path_provider/path_provider.dart';
class ListaCompra extends ChangeNotifier {
  final _productos = <Producto>[];
  List<Producto> get productos => List.unmodifiable(_productos);
  void borraProducto(int indice) {
    _productos.removeAt(indice);
    notifyListeners();
  }
  void anadeProducto(Producto item) {
    _productos.add(item);
    _salvaProductos();
    notifyListeners();
  }
  void actualizaProducto(Producto item, int indice) {
    _productos[indice] = item;
    notifyListeners();
  }
  void marcaCompletado(int indice, bool completado) {
    final producto = _productos[indice];
    _productos[indice] = producto.copiaSiNulo(completado: completado);
    notifyListeners();
  }
  Future<String> get _localPath async {
    final directory = await getApplicationDocumentsDirectory();
    return directory.path;
  }

  Future<File> get _localFile async {
    final path = await _localPath;
    return File('$path/productos.json');
  }

  Future<void> _salvaProductos() async {
    final file = await _localFile;
    var cadena = '[\n';
    for (int i=0; i<_productos.length; i++) {
      cadena += _productos[i].aJson();
      if (i<_productos.length-1) {
        cadena += ',\n';
      } else {
        cadena += '\n';
      }
    }
    cadena += ']';
    file.writeAsString(cadena);
  }

  Future<void> _leeProductos() async {
    try {
      final file = await _localFile;
      final productosString = await file.readAsString();
      final List<dynamic> productosJson = jsonDecode(productosString);
      for (var prodJson in productosJson) {
        _productos.add(Producto.desdeJson(prodJson));
      }
      notifyListeners();
    } on FileSystemException catch (e) {
      return;
    }
  }

  void init() {
    _leeProductos();
  }
}