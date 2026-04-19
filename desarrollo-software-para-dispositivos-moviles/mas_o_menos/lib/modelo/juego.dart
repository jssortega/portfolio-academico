import 'dart:math';

import 'package:flutter/material.dart';

enum Dificultad{
  Facil(rango: 50,maxIntentos: 10, penalizacionPuntuacion: 15),
  Normal(rango: 100,maxIntentos: 15,penalizacionPuntuacion: 5),
  Dificil(rango: 500,maxIntentos: 20, penalizacionPuntuacion: 2),
  Challenge(rango: 10, maxIntentos: 1,penalizacionPuntuacion: 0);

  const Dificultad({required this.rango,required this.maxIntentos, required this.penalizacionPuntuacion});

  final int rango;
  final int maxIntentos;
  final int penalizacionPuntuacion;

}

class Juego extends ChangeNotifier{
  int _valor = 0;
  int _puntuacion = 100;
  var _pista = const Icon(Icons.first_page_rounded,size: 35,);
  int _numeroAdivinar = 0;
  bool finalJuego = false;
  int _maxIntentos = 0;
  int _numeroIntentos = 0;
  Dificultad _dificultad = Dificultad.Normal;
  String _mensajePista = "";



  int get valor => _valor;
  int get numeroAdivinar => _numeroAdivinar;
  int get puntuacion => _puntuacion;
  get pista => _pista;
  int get maxIntentos => _maxIntentos;
  int get numeroIntentos => _numeroIntentos;
  Dificultad get dificultad => _dificultad;
  String get mensajePista => _mensajePista;


  set valor(nuevoValor) {
    _valor = nuevoValor;
    notifyListeners();
  }

  set maxIntentos(nuevoValor){
    _maxIntentos = nuevoValor;
    notifyListeners();
  }

  set numeroIntentos(nuevoValor){
    _numeroIntentos = nuevoValor;
    notifyListeners();
  }

  set dificultad(nuevaDificultad){
    _dificultad = nuevaDificultad;
    notifyListeners();
  }


  void calculaPuntuacion(){
    _puntuacion = (100 - numeroIntentos*5 - dificultad.penalizacionPuntuacion).toInt();
    notifyListeners();
  }

  void calculaPistaNormal(){
    if(_valor < _numeroAdivinar){
      _pista = const Icon(Icons.arrow_upward_rounded, size: 35,);
    }else if(_valor == _numeroAdivinar){
      finalJuego = true;
    }else{
      _pista = const Icon(Icons.arrow_downward_rounded, size: 35);
    }
    notifyListeners();
  }

  void calculaPistaEspecial(){
    if(numeroAdivinar%2 == 0){
      _mensajePista = "El numero es par";
    } else{
      _mensajePista = "El numero es impar";
    }
    notifyListeners();
  }

  void empiezaJuego(){
    final aleatorio = Random();
    _numeroAdivinar = aleatorio.nextInt(dificultad.rango);
    _valor = 0;
    _puntuacion = 0;
    _pista = const Icon(Icons.first_page_rounded,size: 35,);
    finalJuego = false;
    _maxIntentos = dificultad.maxIntentos;
    _numeroIntentos = 0;
    notifyListeners();
  }

}
