import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import 'package:finance_tfg/utils/global.dart';
import 'package:provider/provider.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class ResumenMesGrafica extends StatefulWidget {
  ResumenMesGrafica({super.key});

  final Color leftBarColor = Color(0xFF24BF8B);
  final Color rightBarColor = Color(0xFFF15858);
  final Color avgColor = Colors.blue;

  @override
  State<StatefulWidget> createState() => ResumenMesGraficaState();
}

class ResumenMesGraficaState extends State<ResumenMesGrafica> {
  final double width = 14.w;

  int touchedGroupIndex = -1;

  @override
  Widget build(BuildContext context) {
    final listaMovimientos = Provider.of<List<Movimiento>?>(context);

    if (listaMovimientos == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final valoresMes = calcularGrafica(listaMovimientos);

    final rawBarGroups = [
      makeGroupData(0, valoresMes['ingresosSemana1']!, -valoresMes['gastosSemana1']!,),
      makeGroupData(1, valoresMes['ingresosSemana2']!, -valoresMes['gastosSemana2']!,),
      makeGroupData(2, valoresMes['ingresosSemana3']!, -valoresMes['gastosSemana3']!,),
      makeGroupData(3, valoresMes['ingresosSemana4']!, -valoresMes['gastosSemana4']!,),
    ];

    final showingBarGroups = getShowingBarGroups(rawBarGroups);

    return AspectRatio(
      aspectRatio: 1,
      child: Padding(
        padding: REdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                makeTransactionsIcon(),
                SizedBox(width: 38.w),
                Text(
                  'Transacciones',
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 22.sp,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                SizedBox(width: 4.w),
                Text(
                  '(Presiona)',
                  style: TextStyle(
                    color: const Color(0xFF828FA2),
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ),
            SizedBox(height: 38.h),
            Expanded(
              child: BarChart(
                BarChartData(
                  maxY: 3000,
                  barTouchData: BarTouchData(
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipColor: (group) {
                        return Colors.blueGrey.withOpacity(0.9);
                      },
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        final valorOriginal =
                            rawBarGroups[groupIndex].barRods[rodIndex].toY;

                        if (touchedGroupIndex == groupIndex) {
                          return BarTooltipItem(
                            '${valorOriginal.toInt()}€\nMedia: ${rod.toY.toInt()}€',
                            TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14.sp,
                            ),
                          );
                        }

                        return BarTooltipItem(
                          '${valorOriginal.toInt()}€',
                          TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 14.sp,
                          ),
                        );
                      },
                    ),
                    touchCallback: (FlTouchEvent event, response) {
                      setState(() {
                        if (!event.isInterestedForInteractions ||
                            response == null ||
                            response.spot == null) {
                          touchedGroupIndex = -1;
                        } else {
                          touchedGroupIndex =
                              response.spot!.touchedBarGroupIndex;
                        }
                      });
                    },
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      axisNameWidget: Text(
                        "Semanas",
                        style: TextStyle(
                          color: Colors.black,
                          fontWeight: FontWeight.bold,
                          fontSize: 18.sp,
                        ),
                      ),
                      axisNameSize: 24.h,
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: bottomTitles,
                        reservedSize: 42.h,
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 36.w,
                        interval: 1,
                        getTitlesWidget: leftTitles,
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: showingBarGroups,
                  gridData: const FlGridData(show: false),
                ),
              ),
            ),
            SizedBox(height: 12.h),
          ],
        ),
      ),
    );
  }

  List<BarChartGroupData> getShowingBarGroups(
      List<BarChartGroupData> rawBarGroups,
      ) {
    final groups = List<BarChartGroupData>.of(rawBarGroups);

    if (touchedGroupIndex == -1) {
      return groups;
    }

    final touchedGroup = groups[touchedGroupIndex];

    var sum = 0.0;

    for (final rod in touchedGroup.barRods) {
      sum += rod.toY;
    }

    final avg = sum / touchedGroup.barRods.length;

    groups[touchedGroupIndex] = touchedGroup.copyWith(
      barRods: touchedGroup.barRods.map((rod) {
        return rod.copyWith(
          toY: avg,
          color: widget.avgColor,
        );
      }).toList(),
    );

    return groups;
  }

  Widget leftTitles(double value, TitleMeta meta) {
    TextStyle style = TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 14.sp,);
    String text;
    if (value == 1000) {
      text = '1K';
    } else if (value == 2000) {
      text = '2K';
    } else if (value == 3000) {
      text = '3K';
    } else {
      return Container();
    }
    return SideTitleWidget(
      meta: meta,
      space: 0,
      child: Text(text, style: style),
    );
  }

  Widget bottomTitles(double value, TitleMeta meta) {
    final titles = <String>['1', '2', '3', '4'];

    final Widget text = Text(
      titles[value.toInt()],
      style: TextStyle(
        color: Colors.black,
        fontWeight: FontWeight.bold,
        fontSize: 14.sp,
      ),
    );

    return SideTitleWidget(
      meta: meta,
      space: 16.h, //margin top
      child: text,
    );
  }

  BarChartRodLabel makeLabel(
      double value,
      Color color,
      bool avg,
      ) =>
      BarChartRodLabel(
        text: value.toString(),
        angle: avg ? -90 : 0,
        style: TextStyle(
          color: color,
          fontSize: 12.sp,
          fontWeight: FontWeight.bold,
          shadows: [
            Shadow(color: Colors.black54, blurRadius: 4),
          ],
        ),
      );

  BarChartGroupData makeGroupData(int x, double y1, double y2) {
    return BarChartGroupData(
      barsSpace: 8.w,
      x: x,
      barRods: [
        BarChartRodData(
          toY: y1,
          color: widget.leftBarColor,
          width: width,
        ),
        BarChartRodData(
          toY: y2,
          color: widget.rightBarColor,
          width: width,
        ),
      ],
    );
  }

  Widget makeTransactionsIcon() {
    double width = 4.5.w;
    double space = 3.5.w;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: width,
          height: 10.h,
          color: Colors.black.withValues(alpha: 0.4),
        ),
        SizedBox(
          width: space,
        ),
        Container(
          width: width,
          height: 28.h,
          color: Colors.black.withValues(alpha: 0.8),
        ),
        SizedBox(
          width: space,
        ),
        Container(
          width: width,
          height: 42.h,
          color: Colors.black.withValues(alpha: 1),
        ),
        SizedBox(
          width: space,
        ),
        Container(
          width: width,
          height: 28.h,
          color: Colors.black.withValues(alpha: 0.8),
        ),
        SizedBox(
          width: space,
        ),
        Container(
          width: width,
          height: 10.h,
          color: Colors.black.withValues(alpha: 0.4),
        ),
      ],
    );
  }

  Map<String, double> calcularGrafica(List<Movimiento> listaMovimientos){

    DateTime fechaActual = DateTime.now();

    Map<String, double> resultado = {
      'gastosSemana1': 0.0,
      'ingresosSemana1': 0.0,
      'gastosSemana2': 0.0,
      'ingresosSemana2': 0.0,
      'gastosSemana3': 0.0,
      'ingresosSemana3': 0.0,
      'gastosSemana4': 0.0,
      'ingresosSemana4': 0.0,
    };


    for(Movimiento movimiento in listaMovimientos){
      if(movimiento.getFecha().month  == fechaActual.month && movimiento.getFecha().year == fechaActual.year){
        switch(movimiento.getFecha().day){
          case >=1 && <=8:
            if(movimiento.getTipoMovimiento() == TipoMovimiento.gasto){
              resultado['gastosSemana1'] = resultado['gastosSemana1']! + movimiento.getImporte();
            }
            else{
                resultado['ingresosSemana1'] = resultado['ingresosSemana1']! + movimiento.getImporte();
            }
            break;
          case >=9 && <=15:
            if(movimiento.getTipoMovimiento() == TipoMovimiento.gasto){
              resultado['gastosSemana2'] = resultado['gastosSemana2']! + movimiento.getImporte();
            }
            else{
              resultado['ingresosSemana2'] = resultado['ingresosSemana2']! + movimiento.getImporte();
            }
            break;
          case >=16 && <=22:
            if(movimiento.getTipoMovimiento() == TipoMovimiento.gasto){
              resultado['gastosSemana3'] = resultado['gastosSemana3']! + movimiento.getImporte();
            }
            else{
              resultado['ingresosSemana3'] = resultado['ingresosSemana3']! + movimiento.getImporte();
            }
            break;
          case >=23 && <=31:
            if(movimiento.getTipoMovimiento() == TipoMovimiento.gasto){
              resultado['gastosSemana4'] = resultado['gastosSemana4']! + movimiento.getImporte();
            }
            else{
              resultado['ingresosSemana4'] = resultado['ingresosSemana4']! + movimiento.getImporte();
            }
            break;
        }
      }
    }

    return resultado;

  }


}