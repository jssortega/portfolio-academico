import 'package:finance_tfg/componentes/graficas/leyenda_categorias_grafica.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/utils/global.dart';

class PieChartSample2 extends StatefulWidget {
  const PieChartSample2({super.key});

  @override
  State<StatefulWidget> createState() => PieChart2State();
}

class PieChart2State extends State {
  int touchedIndex = -1;

  @override
  Widget build(BuildContext context) {
    final listaMovimientos = Provider.of<List<Movimiento>?>(context);
    if (listaMovimientos == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return AspectRatio(
      aspectRatio: 1.3,
      child: Row(
        children: <Widget>[
          SizedBox(height: 18.h),
          Expanded(
            child: AspectRatio(
              aspectRatio: 1,
              child: PieChart(
                PieChartData(
                  pieTouchData: PieTouchData(
                    touchCallback: (FlTouchEvent event, pieTouchResponse) {
                      setState(() {
                        if (!event.isInterestedForInteractions ||
                            pieTouchResponse == null ||
                            pieTouchResponse.touchedSection == null) {
                          touchedIndex = -1;
                          return;
                        }
                        touchedIndex = pieTouchResponse
                            .touchedSection!.touchedSectionIndex;
                      });
                    },
                  ),
                  borderData: FlBorderData(
                    show: false,
                  ),
                  sectionsSpace: 0,
                  centerSpaceRadius: 40.r,
                  sections: showingSections(listaMovimientos),
                ),
              ),
            ),
          ),
          Column(
            mainAxisAlignment: MainAxisAlignment.end,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ...Categoria.values.map(
                (categoria) => Padding(
                  padding: EdgeInsets.only(bottom: 4.h),
                  child: Indicator(
                    color: categoria.colorIcono,
                    text: capitalizarPrimera(categoria.name),
                    isSquare: true,
                  ),
                ),
              ),

              SizedBox(height: 14.h),
            ],
          ),
          SizedBox(width: 28.w),
        ],
      ),
    );
  }

  List<PieChartSectionData> showingSections(List<Movimiento> listaMovimientos) {

    Map<String, double> gastoCategoria = calcularGrafica(listaMovimientos);


    return List.generate(Categoria.values.length, (i) {
      final categoria = Categoria.values[i];

      final isTouched = i == touchedIndex;
      final fontSize = isTouched ? 25.0.sp : 16.0.sp;
      final radius = isTouched ? 60.0.r : 50.0.r;
      const shadows = [Shadow(color: Colors.black, blurRadius: 2)];

      final value = gastoCategoria[categoria.name];

      return PieChartSectionData(
        color: categoria.colorIcono,
        value: value,
        title: '$value%',
        radius: radius,
        titleStyle: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          color: Colors.white,
          shadows: shadows,
        ),
      );
    });
  }

  Map<String, double> calcularGrafica(List<Movimiento> listaMovimientos){

    final Map<String, double> resultado = {
      for (final categoria in Categoria.values) categoria.name: 0.0,
    };

    int totalGastos = 0;

    for(Movimiento movimiento in listaMovimientos){
      if(movimiento.getTipoMovimiento() == TipoMovimiento.gasto){
        totalGastos++;

        final categoria = movimiento.getCategoria();
        resultado[categoria.name] = resultado[categoria.name]! + 1;

      }
    }

    for(final categoria in Categoria.values){
      resultado[categoria.name] = (((resultado[categoria.name]!/totalGastos)*100)*100).roundToDouble() / 100;
    }

    return resultado;

  }
}