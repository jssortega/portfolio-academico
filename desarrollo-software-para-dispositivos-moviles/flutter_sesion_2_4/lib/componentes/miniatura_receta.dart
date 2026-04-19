import 'package:flutter_sesion_2_4/modelo/modelo.dart';
import 'package:flutter/material.dart';

class MiniaturaReceta extends StatelessWidget {
  final RecetaBasica receta;
  const MiniaturaReceta({Key? key, required this.receta}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(6.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 100,
            width: double.infinity,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                receta.urlImagen,
                fit: BoxFit.cover,
              ),
            ),
          ),
          const SizedBox(height: 4,),
          Text(
            receta.nombre,
            maxLines: 1,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}