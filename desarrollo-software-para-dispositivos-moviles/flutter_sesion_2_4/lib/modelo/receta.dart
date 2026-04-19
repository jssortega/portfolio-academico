
class Receta {
  String id;
  String nombre;
  String bebida;
  String categoria;
  String area;
  String urlImagen;
  List<String> ingredientes;
  List<String> cantidades;

  Receta({
    required this.id,
    required this.nombre,
    required this.bebida,
    required this.categoria,
    required this.area,
    required this.urlImagen,
    required this.ingredientes,
    required this.cantidades
  });

  factory Receta.desdeJson(Map<String, dynamic> json) {
    List<String> ingredientesJson = [];
    for(int i=0;i<20;i++){
      ingredientesJson[i] = json['strIngredient$i'];
    }

    List<String> cantidadesJson = [];
    for(int i=0;i<20;i++){
      cantidadesJson[i] = json['strMeasure$i'];
    }


    return Receta(
      id: json['idMeal'],
      nombre: json['strMeal'],
      bebida: json['strDrinkAlternate'],
      categoria: json['strCategory'],
      area: json['strArea'],
      urlImagen: json['strMealThumb'],
      ingredientes: ingredientesJson,
      cantidades: cantidadesJson
    );
  }
}