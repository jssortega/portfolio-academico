#include <cstdlib>
#include "cmath"

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
   _instancia->camara.set ( IGV_PARALELA, { 3.0, 2.0, 4 }, { 0, 0, 0 }
                          , { 0, 1.0, 0 }, -1 * 1.5, 1 * 1.5, -1 * 1.5, 1 * 1.5
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
{
   // inicializaci�n de las variables de la interfaz
   ancho_ventana = _ancho_ventana;
   alto_ventana = _alto_ventana;

   // inicializaci�n de la ventana de visualizaci�n
   glutInit ( &argc, argv );
   glutInitDisplayMode ( GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH );
   glutInitWindowSize ( _ancho_ventana, _alto_ventana );
   glutInitWindowPosition ( _pos_X, _pos_Y );
   glutCreateWindow ( _titulo.c_str () );

   glEnable ( GL_DEPTH_TEST ); // activa el ocultamiento de superficies por z-buffer
   glClearColor ( 0.0, 0, 0.0, 0.0 ); // establece el color de fondo de la ventana

   glEnable ( GL_LIGHTING ); // activa la iluminaci�n de la escena
   glEnable ( GL_NORMALIZE ); // normaliza los vectores normales para c�lculo iluminaci�n

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
{  switch ( key )
   {
       case 'i': ///< Baja el brazo izquierdo
           if (_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() < 85) {
               _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() + 5);

               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),
                                                                 _instancia->escena.getMallaCilindro());
           }
           break;
       case 'I': ///< Sube el brazo izquierdo
           if (_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() > -85) {
               _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() - 5);

               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),
                                                                 _instancia->escena.getMallaCilindro());
           }
           break;
       case 'd': ///< Baja el brazo derecho
           if (_instancia->escena.getMallaCuadrado()->getAngBrazoDer() > -85) {
               _instancia->escena.getMallaCuadrado()->setAngBrazoDer(_instancia->escena.getMallaCuadrado()->getAngBrazoDer() - 5);

               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),
                                                                 _instancia->escena.getMallaCilindro());
           }
           break;
       case 'D': ///< Sube el brazo derecho
           if (_instancia->escena.getMallaCuadrado()->getAngBrazoDer() < 85) {
               _instancia->escena.getMallaCuadrado()->setAngBrazoDer(_instancia->escena.getMallaCuadrado()->getAngBrazoDer() + 5);
               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),
                                                                 _instancia->escena.getMallaCilindro());
           }
           break;
       case 'c':
       case 'C': ///< Hace la acción de correr
           if ( _instancia->escena.getMallaCuadrado()->getAngPiernaDer() < 60 && _instancia->escena.getMallaCuadrado()->getAngPiernaIzq() > -60 && !_instancia->revertirCorrer) {
               _instancia->escena.getMallaCuadrado()->setAngPiernaDer(_instancia->escena.getMallaCuadrado()->getAngPiernaDer() + 5);
               _instancia->escena.getMallaCuadrado()->setAngPiernaIzq(_instancia->escena.getMallaCuadrado()->getAngPiernaIzq() - 5);
               _instancia->escena.getMallaCuadrado()->setAngZapaDer(_instancia->escena.getMallaCuadrado()->getAngZapaDer() + 4);
               _instancia->escena.getMallaCuadrado()->setAngZapaIzq(_instancia->escena.getMallaCuadrado()->getAngZapaIzq() - 3.9);
               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),
                                                                 _instancia->escena.getMallaCilindro());
               if (_instancia->escena.getMallaCuadrado()->getAngPiernaDer() >= 60 || _instancia->escena.getMallaCuadrado()->getAngPiernaIzq() <= -60 )
                   _instancia->revertirCorrer=true;

           }else if(_instancia->escena.getMallaCuadrado()->getAngPiernaDer() > -60 && _instancia->escena.getMallaCuadrado()->getAngPiernaIzq() < 60 && _instancia->revertirCorrer){
               _instancia->escena.getMallaCuadrado()->setAngPiernaDer(_instancia->escena.getMallaCuadrado()->getAngPiernaDer() - 5);
               _instancia->escena.getMallaCuadrado()->setAngPiernaIzq(_instancia->escena.getMallaCuadrado()->getAngPiernaIzq() + 5);
               _instancia->escena.getMallaCuadrado()->setAngZapaDer(_instancia->escena.getMallaCuadrado()->getAngZapaDer() - 4);
               _instancia->escena.getMallaCuadrado()->setAngZapaIzq(_instancia->escena.getMallaCuadrado()->getAngZapaIzq() + 3.9);
               _instancia->escena.getMallaCilindro()->visualizar(_instancia->escena.getMallaCuadrado(),

                                                                 _instancia->escena.getMallaCilindro());
               if (_instancia->escena.getMallaCuadrado()->getAngPiernaDer() <= -60 || _instancia->escena.getMallaCuadrado()->getAngPiernaIzq() >= 60 )
                   _instancia->revertirCorrer=false;
           }
           break;
       case 'A':
       case 'a': ///< Empieza la animación
           _instancia->animacion = true;
           break;
       case 'v':
       case 'V': ///< Cambia de vista
         switch (++_instancia->cambioVista) {
             case 1:
                 _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={0.5,0,2}, _instancia->r= {0.5,0,0}, _instancia->V={0,1,0}, -1 * 2, 1 * 2, -1 * 2, 1 * 2, 1, 200 );
                 _instancia->camara.aplicar();
                 break;
             case 2:
                 _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={0.5,2,0.25}, _instancia->r= {0.5,0,0.25}, _instancia->V={1,0,0}, -1 * 2, 1 * 2, -1 * 2, 1 * 2, 1, 200 );
                 _instancia->camara.aplicar();
                 break;
             case 3:
                 _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={5,0.5,0.25}, _instancia->r= {0,0.5,0.25}, _instancia->V={0,1,0}, -1 * 2, 1 * 2, -1 * 2, 1 * 2, 1, 200 );
                 _instancia->camara.aplicar();
                 break;
             case 4:
                 _instancia->camara.set ( IGV_PARALELA, _instancia->p0 ={3, 2, 4}, _instancia->r= {0,0,0}, _instancia->V={0, 1.0, 0}, -1 * 1.5, 1 * 1.5, -1 * 1.5, 1 * 1.5, -3, 200 );
                 _instancia->camara.aplicar();
                 _instancia->cambioVista = 0;
                 break;
         }
           break;
       case '+': ///< Acerca el zoom
           _instancia->camara.zoom(-5);
           _instancia->camara.aplicar();
           break;
       case '-': ///< Aleja el zoom
           _instancia->camara.zoom(5);
           _instancia->camara.aplicar();
           break;
      case 'e': ///< activa/desactiva la visualizacion de los ejes
         _instancia->escena.set_ejes ( !_instancia->escena.get_ejes () );
         break;
      case 27: ///< tecla de escape para SALIR
         exit ( 1 );
   }
   glutPostRedisplay (); // renueva el contenido de la ventana de visi�n
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
   // guardamos valores nuevos de la ventana de visualizaci�n
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
    glViewport ( 0, 0, _instancia->get_ancho_ventana (), _instancia->get_alto_ventana () );

    // comprueba el modo para s�lo visualizar o seleccionar:
    if ( _instancia->modo == IGV_SELECCIONAR )
    {   ///< dibuja la escena sin efectos, sin iluminaci�n, sin texturas ...
        glDisable ( GL_LIGHTING ); // desactiva la iluminaci�n de la escena
        glDisable ( GL_DITHER );

        glClear ( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );
        glDisable ( GL_TEXTURE_2D );
        glDisable ( GL_CULL_FACE );

        ///< aplica la c�mara y visualiza la escena
        _instancia->camara.aplicar();
        _instancia->escena.visualizar();
        ///< Obtiene el color del pixel seleccionado
        GLubyte pixelColor[3];
        glReadPixels(_instancia->cursorX,_instancia->get_alto_ventana()-_instancia->cursorY,1,1,GL_RGB,GL_UNSIGNED_BYTE,pixelColor);
        ///< Comprueba el color del objeto que hay en el cursor es del brazo izquierdo
        float p = 0.890196;
        if (_instancia->comparaColor((float)pixelColor[0]/255,0.9,1) && (float)pixelColor[1]/255 == 1 && (float)pixelColor[2]/255 == 0)
            _instancia->objeto_seleccionado = 0;

        ///< Compruba si está el objeto seleccionado y lo mueve según la posición del ratón
        if(_instancia->objeto_seleccionado == 0) {
            _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() + _instancia->cursorXX);
            _instancia->escena.getMallaCuadrado()->visualizar(_instancia->escena.getMallaCuadrado(),_instancia->escena.getMallaCilindro());
        }

        ///< Cambia a modo de visualizaci�n de la escena
        _instancia->modo = IGV_VISUALIZAR;
        ///< Habilita de nuevo la iluminaci�n
        glEnable ( GL_LIGHTING );
    }
    else
    {   ///< aplica las transformaciones en funci�n de los par�metros de la c�mara
        _instancia->camara.aplicar();

        ///< visualiza la escena
        _instancia->escena.visualizar();

        ///< refresca la ventana
        glutSwapBuffers ();
    }
}


void igvInterfaz::mouseFunc ( GLint boton, GLint estado, GLint x, GLint y )
{   ///< comprueba que se ha pulsado el bot�n izquierdo
    if(boton == GLUT_LEFT_BUTTON){
        /** guarda que el bot�n se ha presionado o se ha soltado.
           Si se ha pulsado hay que pasar a modo IGV_SELECCIONAR */
        if(estado == GLUT_DOWN) {
            _instancia->modo = IGV_SELECCIONAR;
        }

        ///< guarda el pixel pulsado
        _instancia->cursorX = x;
        _instancia->cursorY = y;
        ///< renueva el contenido de la ventana de vision
        _instancia->displayFunc();
    }

}

/**
 * M�todo para el control del desplazamiento del rat�n con un bot�n pulsado
 * @param x Coordenada X de la posici�n del cursor del rat�n en la ventana
 * @param y Coordenada Y de la posici�n del cursor del rat�n en la ventana
 * @post Se actualiza el estado de la interfaz
 */
void igvInterfaz::motionFunc ( GLint x, GLint y ){
    if (_instancia->objeto_seleccionado != -1) {
        ///< Calcular el ángulo de rotación basado en el movimiento del ratón
        float rotationAngleY = (y - _instancia->cursorY);

        ///< Almacena el angulo de rotación para aplicarlo en displayfunc()
        _instancia->cursorXX = rotationAngleY;

        ///< Guardar las nuevas coordenadas del ratón
        _instancia->cursorX = x;
        _instancia->cursorY = y;

        ///< Volver a dibujar la escena para visualizar la rotación
        glutPostRedisplay();
    }
}


/**
 * M�todo para animar la escena
 */
void igvInterfaz::idleFunc () {
    ///< Comprueba que se ha pulsado la tecla a para comemnzar la animación
    if(_instancia->animacion) {

        _instancia->contadorAnimación++;

        ///< Se establece el punto de partida de la animación
        _instancia->escena.getMallaCuadrado()->setAngBrazoDer(0);
        _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(0);
        _instancia->escena.getMallaCuadrado()->setAngPiernaDer(0);
        _instancia->escena.getMallaCuadrado()->setAngPiernaIzq(0);
        _instancia->escena.getMallaCuadrado()->setAngZapaDer(0);
        _instancia->escena.getMallaCuadrado()->setAngZapaIzq(0);

        _instancia->tiempo += 8;

        ///< Se ajustan las velocidades de la escena
        float velocidadBrazo1 = 0.00043;
        float velocidadBrazo2 = 0.00043;
        float velocidadPiernas = 0.02;
        float velocidadSombrero = 0.000004;

        float anguloBrazo = -80 * sin(velocidadBrazo1 * _instancia->tiempo);
        float anguloBrazo2 = -60 * sin(velocidadBrazo2 * _instancia->tiempo);
        float anguloPiernaIzq = -25 * sin(velocidadPiernas * _instancia->tiempo);
        float anguloPiernaDer = +25 * sin(velocidadPiernas * _instancia->tiempo);
        float movSombreroX = -0.03 * sin(velocidadSombrero * _instancia->tiempo);
        float movSombreroY = 0.0175 * sin(velocidadSombrero * _instancia->tiempo);

        switch (_instancia->estado) {
            case 0: ///< Comienza a correr
                _instancia->escena.getMallaCuadrado()->setAngPiernaIzq(_instancia->escena.getMallaCuadrado()->getAngPiernaIzq() + anguloPiernaIzq);
                _instancia->escena.getMallaCuadrado()->setAngPiernaDer(_instancia->escena.getMallaCuadrado()->getAngPiernaDer() + anguloPiernaDer);
                _instancia->escena.getMallaCuadrado()->setAngZapaIzq(_instancia->escena.getMallaCuadrado()->getAngZapaIzq() + anguloPiernaIzq);
                _instancia->escena.getMallaCuadrado()->setAngZapaDer(_instancia->escena.getMallaCuadrado()->getAngZapaDer() + anguloPiernaDer);
                break;
            case 1: ///< baja el brazo para coger el gorro
                _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() + anguloBrazo);
                break;
            case 2: ///< lo coje y lo lanza
                if (_instancia->escena.getMallaCuadrado()->getAngBrazoIzq() >= 0) {
                    _instancia->escena.getMallaCuadrado()->setAngBrazoIzq(
                            _instancia->escena.getMallaCuadrado()->getAngBrazoIzq() + anguloBrazo2);
                    _instancia->escena.getMallaCuadrado()->setGorroX(
                            _instancia->escena.getMallaCuadrado()->getGorroX() + movSombreroX);
                    _instancia->escena.getMallaCuadrado()->setGorroY(
                            _instancia->escena.getMallaCuadrado()->getGorroY() + movSombreroY);
                }
                break;
        }

        if (_instancia->estado != 3) {
            if (_instancia->contadorAnimación == 700) {
                _instancia->estado = (_instancia->estado + 1);
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
    glutIdleFunc ( idleFunc );

   glutDisplayFunc ( displayFunc );

    glutMouseFunc ( mouseFunc );
    glutMotionFunc ( motionFunc );
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

///< Metodo para comparar el color al pulsar el ratón con el del brazo izquierdo
bool igvInterfaz::comparaColor(float color1, float color2, int precision) {
    color1 = roundf(color1 * pow(10, precision)) / pow(10, precision);
    color2 = roundf(color2 * pow(10, precision)) / pow(10, precision);
    return color1 == color2;
}