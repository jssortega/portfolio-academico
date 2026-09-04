import 'dart:io';
import 'package:flutter/material.dart';

class AvatarUsuario extends StatelessWidget {
  final String? imagenPerfil;
  final File? imagenSeleccionada;
  final double radio;
  final double iconSize;

  const AvatarUsuario({super.key, this.imagenPerfil, this.imagenSeleccionada, this.radio = 52, this.iconSize = 50});

  ImageProvider? _obtenerImagenAvatar() {
    if (imagenSeleccionada != null) {
      return FileImage(imagenSeleccionada!);
    }

    if (imagenPerfil != null && imagenPerfil!.isNotEmpty) {
      return NetworkImage(imagenPerfil!);
    }

    return null;
  }

  @override
  Widget build(BuildContext context) {
    final imagenAvatar = _obtenerImagenAvatar();

    return CircleAvatar(
      radius: radio,
      backgroundImage: imagenAvatar,
      child: imagenAvatar == null
          ? Icon(
        Icons.person,
        size: iconSize,
      )
          : null,
    );
  }
}