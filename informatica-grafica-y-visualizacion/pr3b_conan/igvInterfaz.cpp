#include <cstdlib>
#include <stdio.h>
#include <cmath>

#include "igvInterfaz.h"

// Aplicaci�n del patr�n de dise�o Singleton
igvInterfaz* igvInterfaz::_instancia = nullptr;

// M�todos p�blicos ----------------------------------------

/**
 * M�todo para acceder al objeto �nico de la clase, en aplicaci�n del patr�n de
 * dise�o Singleton
 * @return Una referencia al objeto �nico de la clase
 */
igvInterfaz& igvInterfaz::getInstancia ()
{  if ( !_instancia )
   {  _instancia = new igvInterfaz;
   }

   return *_instancia;
}

/**
 * Crea el mundo que se visualiza en la ventana
 */
void igvInterfaz::crear_mundo ()
{  // inicia la c�mara
   _instancia->camara.set ( IGV_PARALELA, { 6.0, 4.0, 8 }, { 0, 0, 0 }
                            , { 0, 1.0, 0 }, -1 * 5, 1 * 5, -1 * 5, 1 * 5
                            , -1 * 3, 200 );
}

/**
 * Inicializa todos los par�metros para crear una ventana de visualizaci�n
 * @param argc N�mero de par�metros por l�nea de comandos al ejecutar la
 *             aplicaci�n
 * @param argv Par�metros por l�nea de comandos al ejecutar la aplicaci�n
 * @param _ancho_ventana Ancho inicial de la ventana de visualizaci�n
 * @param _alto_ventana Alto inicial de la ventana de visualizaci�n
 * @param _pos_X Coordenada X de la posici�n inicial de la ventana de
 *               visualizaci�n
 * @param _pos_Y Coordenada Y de la posici�n inicial de la ventana de
 *               visualizaci�n
 * @param _titulo T�tulo de la ventana de visualizaci�n
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 * @post Cambia el alto y ancho de ventana almacenado en el objeto
 */
void igvInterfaz::configura_entorno ( int argc, char **argv, int _ancho_ventana
                                      , int _alto_ventana, int _pos_X, int _pos_Y
                                      , std::string _titulo )
{  // inicializaci�n de las variables de la interfaz
   ancho_ventana = _ancho_ventana;
   alto_ventana = _alto_ventana;

   // inicializaci�n de la ventana de visualizaci�n
   glutInit ( &argc, argv );
   glutInitDisplayMode ( GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH );
   glutInitWindowSize ( _ancho_ventana, _alto_ventana );
   glutInitWindowPosition ( _pos_X, _pos_Y );
   glutCreateWindow ( _titulo.c_str () );

   glEnable ( GL_DEPTH_TEST ); // activa el ocultamiento de superficies por z-buffer
   glClearColor ( 1.0, 1.0, 1.0, 0.0 ); // establece el color de fondo de la ventana

   glEnable ( GL_LIGHTING ); // activa la iluminacion de la escena
   glEnable ( GL_NORMALIZE ); // normaliza los vectores normales para calculo iluminacion

   crear_mundo (); // crea el mundo a visualizar en la ventana
}

/**
 * M�todo para visualizar la escena y esperar a eventos sobre la interfaz
 */
void igvInterfaz::inicia_bucle_visualizacion ()
{  glutMainLoop (); // inicia el bucle de visualizaci�n de GLUT
}

/**
 * M�todo para control de eventos del teclado
 * @param key C�digo de la tecla pulsada
 * @param x Coordenada X de la posici�n del cursor del rat�n en el momento del
 *          evento de teclado
 * @param y Coordenada Y de la posici�n del cursor del rat�n en el momento del
 *          evento de teclado
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 * @post Los atributos de la clase pueden cambiar, dependiendo de la tecla pulsada
 */
void igvInterfaz::keyboardFunc ( unsigned char key, int x, int y )
{

    switch ( key )
   {
      // TODO: Apartado C: incluir aqu� el cambio de la c�mara para mostrar las vistas planta, perfil, alzado o perspectiva
      // TODO: Apartado C: incluir aqu� la modificaci�n de los grados de libertad del modelo pulsando las teclas correspondientes

       case 'b': //Movimiento del cuerpo hacia abajo
           if(_instancia->escena.getCuerpo()<32)
                _instancia->escena.setCuerpo(_instancia->escena.getCuerpo() + 4);
           break;
       case 'B': //Movimiento del cuerpo hacia arriba
           if(_instancia->escena.getCuerpo()>0)
               _instancia->escena.setCuerpo(_instancia->escena.getCuerpo() - 4);
           break;
       case 'g': //Movimiento de las "piernas" hacia un sentido
           if(_instancia->escena.getGiPierDer() < 35 || _instancia->escena.getGiPierIzq() > 0) {
               _instancia->escena.setGiPierDer(_instancia->escena.getGiPierDer() + 5);
               _instancia->escena.setGiPierIzq(_instancia->escena.getGiPierIzq() - 5);
           }
           break;
       case 'G': //Movimiento de las "piernas" hacia el sentido contrario
           if(_instancia->escena.getGiPierDer() > 0 || _instancia->escena.getGiPierIzq() < 35) {
               _instancia->escena.setGiPierDer(_instancia->escena.getGiPierDer() - 5);
               _instancia->escena.setGiPierIzq(_instancia->escena.getGiPierIzq() + 5);
           }
           break;
       case 't': //Movimiento para tirar el vaso
           _instancia->escena.setAngVaso(90);
           break;
       case 'T': //Movimiento para poner el vaso de pie otra vez
           _instancia->escena.setAngVaso(0);
           break;
       case 'a': //Empieza la animación
           _instancia->animacion = true;
           break;
      case 'e': // activa/desactiva la visualizacion de los ejes
         _instancia->escena.set_ejes ( !_instancia->escena.get_ejes () );
         break;
       case 'v':
       case 'V': //Cambia de vista
           switch (++_instancia->contadorB) {
               case 1:
                   _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={0,3,5}, _instancia->r= {0,3,0}, _instancia->V={0,1,0}, -1 * 5, 1 * 5, -1 * 5, 1 * 5, 1, 200 );
                   _instancia->camara.aplicar();
                   break;
               case 2:
                   _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={0,5,0}, _instancia->r= {0,0,0}, _instancia->V={1,0,0}, -1 * 5, 1 * 5, -1 * 5, 1 * 5, 1, 200 );
                   _instancia->camara.aplicar();
                   break;
               case 3:
                   _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={5,3,0}, _instancia->r= {0,3,0}, _instancia->V={0,1,0}, -1 * 5, 1 * 5, -1 * 5, 1 * 5, 1, 200 );
                   _instancia->camara.aplicar();
                   break;
               case 4:
                   _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={6, 4, 8}, _instancia->r= {0,0,0}, _instancia->V={0, 1.0, 0}, -1 * 5, 1 * 5, -1 * 5, 1 * 5, 3, 200 );
                   _instancia->camara.aplicar();
                   _instancia->contadorB = 0;
                   break;
           }
           break;
      case 27: // tecla de escape para SALIR
         exit ( 1 );
         break;
   }
   glutPostRedisplay (); // renueva el contenido de la ventana de vision
}

/**
 * M�todo que define la c�mara de visi�n y el viewport. Se llama autom�ticamente
 * cuando se cambia el tama�o de la ventana.
 * @param w Nuevo ancho de la ventana
 * @param h Nuevo alto de la ventana
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 */
void igvInterfaz::reshapeFunc ( int w, int h )
{  // dimensiona el viewport al nuevo ancho y alto de la ventana
   // guardamos valores nuevos de la ventana de visualizacion
   _instancia->set_ancho_ventana ( w );
   _instancia->set_alto_ventana ( h );

   // establece los par�metros de la c�mara y de la proyecci�n
   _instancia->camara.aplicar ();
}

/**
 * M�todo para visualizar la escena
 */
void igvInterfaz::displayFunc ()
{  glClear ( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT ); // borra la ventana y el z-buffer
   // se establece el viewport
   glViewport ( 0, 0, _instancia->get_ancho_ventana ()
                , _instancia->get_alto_ventana () );


   // aplica las transformaciones en funci�n de los par�metros de la c�mara
   _instancia->camara.aplicar ();
   // visualiza la escena
   _instancia->escena.visualizar ();

   // refresca la ventana
   glutSwapBuffers ();
}

/**
 * M�todo para animar la escena
 */
void igvInterfaz::idleFunc () {  // TODO: Apartado D: incluir el c�digo para animar el modelo de la manera m�s realista posible

    if(_instancia->animacion) {

        _instancia->contadorAnimación++;

        _instancia->escena.setCuerpo(16);
        _instancia->escena.setGiPierIzq(0);
        _instancia->escena.setGiPierDer(0);

        _instancia->tiempo += 8;

        float velocidadCuerpo = 0.007;
        float velocidadPiernas = 0.01;
        float velocidadVaso = 0.00025;


        float anguloCuerpo = -18 * sin(velocidadCuerpo * _instancia->tiempo);
        float anguloPiernaIzq= -20 * sin(velocidadPiernas * _instancia->tiempo);
        float anguloPiernaDer= +20 * sin(velocidadPiernas * _instancia->tiempo);
        float movVaso = -5 * sin(velocidadVaso * _instancia->tiempo);

        switch (_instancia->estado) {
            case 0: //Comienza a correr y se va acercando al vaso
                _instancia->escena.setMovVaso(5.5);
                _instancia->escena.setCuerpo(0);
                _instancia->escena.setGiPierIzq(_instancia->escena.getGiPierIzq() + anguloPiernaIzq);
                _instancia->escena.setGiPierDer(_instancia->escena.getGiPierDer() + anguloPiernaDer);
                _instancia->escena.setMovVaso(_instancia->escena.getMovVaso() + movVaso);
                break;
            case 1: //Comienza a beber del vaso
                _instancia->escena.setCuerpo(_instancia->escena.getCuerpo()+  anguloCuerpo);
                break;
            case 2: //Acaba tirando el vaso y por tanto para de beber
                _instancia->escena.setAngVaso(90);
                break;
        }

        if(_instancia->estado !=2) {
            if (_instancia->contadorAnimación == 700) {
                _instancia->estado = (_instancia->estado + 1) % 3;
                _instancia->contadorAnimación = 0;
            }
        }
    }

    glutPostRedisplay();
}
/**
 * M�todo para inicializar los callbacks GLUT
 */
void igvInterfaz::inicializa_callbacks ()
{  glutKeyboardFunc ( keyboardFunc );
   glutReshapeFunc ( reshapeFunc );
   glutDisplayFunc ( displayFunc );
   glutIdleFunc ( idleFunc );
}

/**
 * M�todo para consultar el ancho de la ventana de visualizaci�n
 * @return El valor almacenado como ancho de la ventana de visualizaci�n
 */
int igvInterfaz::get_ancho_ventana ()
{  return ancho_ventana;
}

/**
 * M�todo para consultar el alto de la ventana de visualizaci�n
 * @return El valor almacenado como alto de la ventana de visualizaci�n
 */
int igvInterfaz::get_alto_ventana ()
{  return alto_ventana;
}

/**
 * M�todo para cambiar el ancho de la ventana de visualizaci�n
 * @param _ancho_ventana Nuevo valor para el ancho de la ventana de visualizaci�n
 * @pre Se asume que el par�metro tiene un valor v�lido
 * @post El ancho de ventana almacenado en la aplicaci�n cambia al nuevo valor
 */
void igvInterfaz::set_ancho_ventana ( int _ancho_ventana )
{  ancho_ventana = _ancho_ventana;
}

/**
 * M�todo para cambiar el alto de la ventana de visualizaci�n
 * @param _alto_ventana Nuevo valor para el alto de la ventana de visualizaci�n
 * @pre Se asume que el par�metro tiene un valor v�lido
 * @post El alto de ventana almacenado en la aplicaci�n cambia al nuevo valor
 */
void igvInterfaz::set_alto_ventana ( int _alto_ventana )
{  alto_ventana = _alto_ventana;
}



