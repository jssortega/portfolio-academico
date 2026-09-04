# Informe Ordinaria II

## 1. Identificación

**Proyecto:** TicTacToe

**Repositorio:** http://suleiman.ujaen.es:8011/joc00023/tictactoe-nivel1/-/tree/ordinaria-ii

**Rama de entrega:** `ordinaria-ii`

**Estudiante:** Jesús Ortega Castillo

**Cuenta UJA:** [joc00023@red.ujaen.es](mailto:joc00023@red.ujaen.es)

**Cuenta GitLab:** joc00023

## 2. Punto de partida

El trabajo de Ordinaria II parte de la entrega original del proyecto, correspondiente al siguiente commit de la rama entrega/implementacion:

```text
da06157fd4d74e689280683564ec3600e62ff8c1
```

Ya que en mi caso tengo tres ramas principales, la rama `entrega/analisis-diseno` y la rama `entrega/implementacion` las cuales el último commit de ambas corresponde con el de la entrega dentro de su plazo.
Por otro lado, tengo la rama `examen-ssmmaa` la cual corresponde a los cambios y adaptaciones que hice a partir de la última entrega, y esos cambios están contemplados en esta rama de `ordianria-ii`

La rama utilizada para esta convocatoria es:

```text
ordinaria-ii
```

En este proyecto, parte del trabajo funcional desarrollado previamente en la rama `examen-ssmmaa` se ha incorporado a la rama `ordinaria-ii` para que la entrega final quede localizada en la rama exigida por la convocatoria.

## 3. Cambios realizados

### 3.1. Cambios funcionales

* He incorporado todas las actualizaciones requeridas por el profesor que ha ido implementando.
* He actualizado la ontología en función a los cambios que iba teniendo.
* He actualizado la forma en la que se creaban los `conversation-id` tal como especifica la ontología.
* He mejorado la permanencia del agente jugador para evitar que se desconecten cuando son rechazados.
* He adaptado mis agentes para que pasen los tests proporcionados por el profesor.
* He implementado una mejora a la hora de la inscripción de los jugadores en los tableros para que no repitan siempre el mismo tablero, añadiendo aleatoriedad a la hora de su selección.

### 3.2. Cambios de configuración

* Se ha revisado la configuración de `config.yaml`.
* Se ha revisado la configuración de `agents.yaml`.
* Se han mantenido o actualizado los parámetros necesarios para el arranque del sistema.

### 3.3. Cambios en documentación

* Se ha añadido este informe local `INFORME-ORDINARIA-II.md`.
* Se ha documentado el punto de partida y el alcance de los cambios realizados.

## 4. Consideraciones importantes

Quiero insistir en lo siguiente sobre las 4 ramas que tengo en el repositorio, ya que la rama main la he preferido dejar por defecto y organizar mi proyecto en el resto de ramas.

### Rama entrega/analisis-diseno

Esta rama contiene el analisis y diseño que realicé del proyecto previo a su implementación, en concreto se encuentra en el archivo que tiene llamado `Analisis-diseno.md`.

Esta entrega la hice en su fecha correspondiente y el commit que quiero que se evalue es el último, que está dentro de la fecha margen que había para su entrega.

### Rama entrega/implementacion

Esta rama contiene la primera implementación que hice del proyecto, que debido a todos los cambios que hubo posteriormente ha quedado desactualizada, aunque el commit último también está dentro del plazo de entrega que había, pero no funciona correctamente, ya que esa implementación ha quedado desactualizada.

### Rama examen-ssmmaa

Esta rama sí que contiene la implementación actualizada con todos los cambios que se han ido incorporando por parte del profesor, es la que funciona y la que debería de ser evaluada junto a esta, de ambos el último commit, que es el más actualizado.

### Rama ordinaria-ii

Es la correspondiente a la entrega ordinaria y como he dicho anteriormente contiene el proyecto en su última versión, en el último commit que es el que quiero que se evalúe. Funciona tanto los tests, como mostraré en el siguiente punto, como la ejecución.

## 5. Instrucciones de ejecución

Para ejecutar el proyecto, en primer lugar es necesario que esté el supervisor en ejecución, y un entorno virtual activo, entonces basta con ejecutar:

```bash
python main.py
```

Para ejecutar los tests que proporciona el profesor hay que ejecutar lo siguiente, tal como tengo el proyecto los pasa todos (salida de terminal pegada a continuación):

```bash
pytest .\tests\test_cierre_ordenado_examen.py -v
pytest .\tests\test_configuracion_examen.py -v
pytest .\tests\test_factoria_jid.py -v
pytest .\tests\test_generacion_agentes.py -v
pytest .\tests\test_nicks_alumno.py -v
pytest .\tests\test_normalizacion_salas.py -v
pytest .\tests\test_protocolo_informe.py -v
pytest .\tests\test_protocolo_partida.py -v
pytest .\tests\test_protocolo_registro.py -v
pytest .\tests\test_sonda_supervisor.py -v
```

La salida que debe de dar es la siguiente, ya que pasan todos los tests:

```bash
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_cierre_ordenado_examen.py -v                                                                        
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache                                                                                                                              
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini                                                                                                                   
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0  
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function                   
collected 14 items                                                                                                                                                                 

tests/test_cierre_ordenado_examen.py::TestExtraerCodigosEstadoMuc::test_extrae_varios_codigos PASSED                                                                         [  7%]
tests/test_cierre_ordenado_examen.py::TestExtraerCodigosEstadoMuc::test_extrae_codigo_unico PASSED                                                                           [ 14%]
tests/test_cierre_ordenado_examen.py::TestExtraerCodigosEstadoMuc::test_sin_elemento_x_devuelve_conjunto_vacio PASSED                                                        [ 21%]
tests/test_cierre_ordenado_examen.py::TestExtraerCodigosEstadoMuc::test_elemento_x_sin_status_devuelve_conjunto_vacio PASSED                                                 [ 28%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_fin_de_examen_detectado[codigos0] PASSED                                                                       [ 35%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_fin_de_examen_detectado[codigos1] PASSED                                                                       [ 42%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_fin_de_examen_detectado[codigos2] PASSED                                                                       [ 50%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_no_es_fin_de_examen[codigos0] PASSED                                                                           [ 57%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_no_es_fin_de_examen[codigos1] PASSED                                                                           [ 64%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_no_es_fin_de_examen[codigos2] PASSED                                                                           [ 71%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_no_es_fin_de_examen[codigos3] PASSED                                                                           [ 78%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_no_es_fin_de_examen[codigos4] PASSED                                                                           [ 85%]
tests/test_cierre_ordenado_examen.py::TestEsFinDeExamen::test_salida_de_otro_ocupante_no_detiene_al_agente PASSED                                                            [ 92%]
tests/test_cierre_ordenado_examen.py::TestRegistroDelManejador::test_registra_manejador_de_presencia PASSED                                                                  [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Cierre ordenado examen     │          14 │           0 │           0 │          14 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │          14 │           0 │           0 │          14 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 14 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 14 passed in 0.87s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_configuracion_examen.py -v  
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 10 items                                                                                                                                                                 

tests/test_configuracion_examen.py::TestConfiguracionPorSubmodo::test_sonda_activa_devuelve_par_true_vacio PASSED                                                            [ 10%]
tests/test_configuracion_examen.py::TestConfiguracionPorSubmodo::test_grupo_genera_un_tablero_y_un_jugador PASSED                                                            [ 20%]
tests/test_configuracion_examen.py::TestConfiguracionPorSubmodo::test_individual_genera_tres_tableros_y_doce_jugadores PASSED                                                [ 30%]
tests/test_configuracion_examen.py::TestConfiguracionPorSubmodo::test_grupo_resuelve_sala_compartida PASSED                                                                  [ 40%]
tests/test_configuracion_examen.py::TestConfiguracionPorSubmodo::test_individual_resuelve_sala_del_puesto PASSED                                                             [ 50%]
tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_ninguno_resuelve_sin_llm SKIPPED (config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estra...) [ 60%]
tests/test_configuracion_examen.py::TestPerfilLlm::test_seccion_llm_ausente_resuelve_sin_llm SKIPPED (config.yaml no declara la estrategia de nivel 4 en alumno.niveles_...) [ 70%]
tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_activo_vacio_equivale_a_ninguno SKIPPED (config.yaml no declara la estrategia de nivel 4 en alumno.nivele...) [ 80%]
tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_servidor_resuelve_ollama SKIPPED (config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estra...) [ 90%]
tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_inexistente_lanza_error_didactico SKIPPED (config.yaml no declara la estrategia de nivel 4 en alumno.nive...) [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Configuracion examen       │           5 │           0 │           5 │          10 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │           5 │           0 │           5 │          10 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 5 test(s) correctos, 5 omitido(s), 0 incidencias.
-------------------------------------------------------------------------- Detalle de los tests omitidos --------------------------------------------------------------------------
[SKIP] tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_ninguno_resuelve_sin_llm
        Verifica: Con ``llm.perfil_activo: ninguno`` el sistema arranca sin LLM: ``config["llm"]`` es ``None`` y no se exige API key.
        → Skipped: config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, así que las pruebas del perfil LLM se omiten.
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
[SKIP] tests/test_configuracion_examen.py::TestPerfilLlm::test_seccion_llm_ausente_resuelve_sin_llm
        Verifica: Si el config.yaml no incluye la sección ``llm``, el sistema también arranca sin LLM (``config["llm"]`` es ``None``), por compatibilidad con configuraciones antiguas.
        → Skipped: config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, así que las pruebas del perfil LLM se omiten.
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
[SKIP] tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_activo_vacio_equivale_a_ninguno
        Verifica: Un ``perfil_activo`` vacío se trata como ``ninguno``: no se intenta resolver ningún perfil ni se exige API key.
        → Skipped: config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, así que las pruebas del perfil LLM se omiten.
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
[SKIP] tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_servidor_resuelve_ollama
        Verifica: Seleccionar ``servidor`` en el perfil LLM resuelve el proveedor Ollama. El perfil XMPP (también ``servidor``) no interfiere: son dos selectores distintos.
        → Skipped: config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, así que las pruebas del perfil LLM se omiten.
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
[SKIP] tests/test_configuracion_examen.py::TestPerfilLlm::test_perfil_inexistente_lanza_error_didactico
        Verifica: Un perfil LLM desconocido aborta con un mensaje que sugiere ``ninguno`` como alternativa sin LLM.
        → Skipped: config.yaml no declara la estrategia de nivel 4 en alumno.niveles_estrategia. El nivel 4 (LLM) es opcional, así que las pruebas del perfil LLM se omiten.
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
========================================================================== 5 passed, 5 skipped in 0.69s ===========================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_factoria_jid.py -v        
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items                                                                                                                                                                  

tests/test_factoria_jid.py::TestFactoria::test_construir_jid_usa_el_dominio_del_perfil PASSED                                                                                [ 12%]
tests/test_factoria_jid.py::TestFactoria::test_crear_agente_construye_el_jid_desde_la_config PASSED                                                                          [ 25%]
tests/test_factoria_jid.py::TestFactoria::test_crear_agente_no_fija_ningun_jid_literal PASSED                                                                                [ 37%]
tests/test_factoria_jid.py::TestFactoria::test_crear_agente_admite_las_clases_del_alumno PASSED                                                                              [ 50%]
tests/test_factoria_jid.py::TestFactoria::test_arrancar_agente_propaga_auto_register PASSED                                                                                  [ 62%]
tests/test_factoria_jid.py::TestNickEnLaSala::test_agente_se_une_a_la_sala_con_el_nick_de_la_config PASSED                                                                   [ 75%]
tests/test_factoria_jid.py::TestNickEnLaSala::test_tablero_dirige_sus_respuestas_por_nick PASSED                                                                             [ 87%]
tests/test_factoria_jid.py::TestNickEnLaSala::test_jugador_dirige_sus_jugadas_al_nick_del_tablero PASSED                                                                     [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Factoria jid               │           8 │           0 │           0 │           8 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │           8 │           0 │           0 │           8 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 8 test(s) correctos, 0 omitido(s), 0 incidencias.
================================================================================ 8 passed in 9.17s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_generacion_agentes.py -v
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 26 items                                                                                                                                                                 

tests/test_generacion_agentes.py::TestModalidadLaboratorio::test_genera_4_tableros_y_12_jugadores PASSED                                                                     [  3%]
tests/test_generacion_agentes.py::TestModalidadLaboratorio::test_jugadores_se_reparten_uniformemente_entre_3_niveles PASSED                                                  [  7%]
tests/test_generacion_agentes.py::TestModalidadLaboratorio::test_no_redirige_servicio_muc PASSED                                                                             [ 11%]
tests/test_generacion_agentes.py::TestModalidadTorneo::test_genera_1_tablero_y_1_jugador PASSED                                                                              [ 15%]
tests/test_generacion_agentes.py::TestModalidadTorneo::test_jugador_unico_usa_primer_nivel_de_la_lista PASSED                                                                [ 19%]
tests/test_generacion_agentes.py::TestModalidadTorneo::test_no_redirige_servicio_muc PASSED                                                                                  [ 23%]
tests/test_generacion_agentes.py::TestModalidadExamenGrupo::test_genera_1_tablero_y_1_jugador PASSED                                                                         [ 26%]
tests/test_generacion_agentes.py::TestModalidadExamenGrupo::test_redirige_servicio_muc_al_componente_dedicado PASSED                                                         [ 30%]
tests/test_generacion_agentes.py::TestModalidadExamenGrupo::test_apunta_a_sala_local_examen PASSED                                                                           [ 34%]
tests/test_generacion_agentes.py::TestModalidadExamenGrupo::test_jugador_unico_usa_primer_nivel_de_la_lista PASSED                                                           [ 38%]
tests/test_generacion_agentes.py::TestModalidadExamenGrupo::test_clave_resuelta_es_examen_grupo PASSED                                                                       [ 42%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_genera_3_tableros_y_12_jugadores PASSED                                                                [ 46%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_redirige_servicio_muc_al_componente_dedicado PASSED                                                    [ 50%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_apunta_a_sala_pc_del_alumno PASSED                                                                     [ 53%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_jid_completo_apunta_a_pc_del_alumno PASSED                                                             [ 57%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_jugadores_se_reparten_uniformemente_entre_3_niveles PASSED                                             [ 61%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_clave_resuelta_es_examen_individual PASSED                                                             [ 65%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_pc_se_canoniza_a_la_forma_comun PASSED                                                                 [ 69%]
tests/test_generacion_agentes.py::TestModalidadExamenIndividual::test_pc_admite_numeracion_de_tres_cifras PASSED                                                             [ 73%]
tests/test_generacion_agentes.py::TestValidacionEntradas::test_examen_individual_sin_pc_lanza_value_error PASSED                                                             [ 76%]
tests/test_generacion_agentes.py::TestValidacionEntradas::test_examen_submodo_desconocido_lanza_value_error PASSED                                                           [ 80%]
tests/test_generacion_agentes.py::TestValidacionEntradas::test_modalidad_sin_entrada_en_agents_yaml_lanza_value_error PASSED                                                 [ 84%]
tests/test_generacion_agentes.py::TestValidacionEntradas::test_falta_usuario_uja_lanza_value_error PASSED                                                                    [ 88%]
tests/test_generacion_agentes.py::TestPlantillasYaml::test_agents_yaml_declara_los_cuatro_modos PASSED                                                                       [ 92%]
tests/test_generacion_agentes.py::TestPlantillasYaml::test_examen_individual_declara_3_tableros_y_12_jugadores PASSED                                                        [ 96%]
tests/test_generacion_agentes.py::TestPlantillasYaml::test_examen_grupo_declara_1_tablero_y_1_jugador PASSED                                                                 [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Generacion agentes         │          26 │           0 │           0 │          26 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │          26 │           0 │           0 │          26 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 26 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 26 passed in 0.11s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_nicks_alumno.py -v      
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 18 items                                                                                                                                                                 

tests/test_nicks_alumno.py::TestCalcularNickBase::test_usa_nick_tablero_si_esta_definido PASSED                                                                              [  5%]
tests/test_nicks_alumno.py::TestCalcularNickBase::test_usa_nick_jugador_si_esta_definido PASSED                                                                              [ 11%]
tests/test_nicks_alumno.py::TestCalcularNickBase::test_recorta_espacios_del_nick PASSED                                                                                      [ 16%]
tests/test_nicks_alumno.py::TestCalcularNickBase::test_cae_a_usuario_uja_cuando_nick_esta_vacio PASSED                                                                       [ 22%]
tests/test_nicks_alumno.py::TestCalcularNickBase::test_cae_a_usuario_uja_cuando_nick_esta_ausente PASSED                                                                     [ 27%]
tests/test_nicks_alumno.py::TestCalcularNickBase::test_independencia_entre_roles PASSED                                                                                      [ 33%]
tests/test_nicks_alumno.py::TestConstruirNickTablero::test_anade_sufijo_indice_a_partir_de_uno PASSED                                                                        [ 38%]
tests/test_nicks_alumno.py::TestConstruirNickTablero::test_rellena_con_cero_para_un_digito PASSED                                                                            [ 44%]
tests/test_nicks_alumno.py::TestConstruirNickTablero::test_admite_dos_digitos_sin_truncar PASSED                                                                             [ 50%]
tests/test_nicks_alumno.py::TestConstruirNickJugador::test_incluye_nivel_y_indice PASSED                                                                                     [ 55%]
tests/test_nicks_alumno.py::TestConstruirNickJugador::test_independiente_del_indice_de_tablero PASSED                                                                        [ 61%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_inyecta_nick_muc_en_cada_agente PASSED                                                                           [ 66%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_nicks_unicos_dentro_de_la_sala PASSED                                                                            [ 72%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_usa_nick_personalizado_cuando_se_define PASSED                                                                   [ 77%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_cae_a_usuario_uja_cuando_no_hay_nick PASSED                                                                      [ 83%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_los_tableros_no_repiten_nick_entre_ellos PASSED                                                                  [ 88%]
tests/test_nicks_alumno.py::TestGenerarAgentesConNick::test_los_jugadores_distinguen_nivel_e_indice PASSED                                                                   [ 94%]
tests/test_nicks_alumno.py::TestGenerarAgentesGrupo::test_grupo_aplica_el_nick PASSED                                                                                        [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Nicks alumno               │          18 │           0 │           0 │          18 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │          18 │           0 │           0 │          18 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 18 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 18 passed in 0.10s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_normalizacion_salas.py -v
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 26 items                                                                                                                                                                 

tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_variantes_de_puesto_canonizan_a_forma_comun[variantes0-pc-05] PASSED                                        [  3%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_variantes_de_puesto_canonizan_a_forma_comun[variantes1-pc-30] PASSED                                        [  7%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_variantes_de_puesto_canonizan_a_forma_comun[variantes2-pc-01] PASSED                                        [ 11%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[PC-01-pc-01] PASSED                                                  [ 15%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[PC-09-pc-09] PASSED                                                  [ 19%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[PC-10-pc-10] PASSED                                                  [ 23%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[PC-30-pc-30] PASSED                                                  [ 26%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[pc7-pc-07] PASSED                                                    [ 30%]
tests/test_normalizacion_salas.py::TestCanonizacionPuestos::test_numero_de_puesto_relleno_a_dos_digitos[PC-100-pc-100] PASSED                                                [ 34%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[examen-examen] PASSED                                      [ 38%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[EXAMEN-examen] PASSED                                      [ 42%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[ Examen -examen] PASSED                                    [ 46%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[torneo_lab-torneo_lab] PASSED                              [ 50%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[Torneo_Lab-torneo_lab] PASSED                              [ 53%]
tests/test_normalizacion_salas.py::TestCanonizacionOtrosNombres::test_nombres_no_puesto_solo_minusculas_y_recorte[sala_pc01-sala_pc01] PASSED                                [ 57%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[PC-05] PASSED                                                                                 [ 61%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[pc 7] PASSED                                                                                  [ 65%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[examen] PASSED                                                                                [ 69%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[ EXAMEN ] PASSED                                                                              [ 73%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[torneo_lab] PASSED                                                                            [ 76%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_idempotencia[PC_30] PASSED                                                                                 [ 80%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_resultado_listo_para_usar_como_localpart[PC-05] PASSED                                                     [ 84%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_resultado_listo_para_usar_como_localpart[examen] PASSED                                                    [ 88%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_resultado_listo_para_usar_como_localpart[torneo_lab] PASSED                                                [ 92%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_resultado_listo_para_usar_como_localpart[PC-30] PASSED                                                     [ 96%]
tests/test_normalizacion_salas.py::TestPropiedadesGenerales::test_resultado_listo_para_usar_como_localpart[ Pc_7 ] PASSED                                                    [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Normalizacion salas        │          26 │           0 │           0 │          26 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │          26 │           0 │           0 │          26 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 26 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 26 passed in 0.09s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_protocolo_informe.py -v  
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 6 items                                                                                                                                                                  

tests/test_protocolo_informe.py::TestInformeTablero::test_tablero_responde_con_inform_tras_la_partida PASSED                                                                 [ 16%]
tests/test_protocolo_informe.py::TestInformeTablero::test_informe_es_conforme_a_la_ontologia PASSED                                                                          [ 33%]
tests/test_protocolo_informe.py::TestInformeTablero::test_tablero_rechaza_el_informe_si_la_partida_sigue PASSED                                                              [ 50%]
tests/test_protocolo_informe.py::TestInformeTablero::test_informe_de_una_partida_abortada PASSED                                                                             [ 66%]
tests/test_protocolo_informe.py::TestInformeTablero::test_informe_conserva_el_hilo_de_la_solicitud PASSED                                                                    [ 83%]
tests/test_protocolo_informe.py::TestInformeTablero::test_supervisor_aplica_cortesia_de_reintento PASSED                                                                     [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Protocolo informe          │           6 │           0 │           0 │           6 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │           6 │           0 │           0 │           6 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 6 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 6 passed in 28.35s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_protocolo_partida.py -v
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 10 items                                                                                                                                                                 

tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_anuncia_game_start_a_ambos_jugadores PASSED                                                                [ 10%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_convoca_los_turnos_con_cfp PASSED                                                                          [ 20%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_confirma_las_jugadas_con_accept_proposal PASSED                                                            [ 30%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_aborta_si_la_jugada_es_invalida PASSED                                                                     [ 40%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_aborta_si_un_jugador_no_responde PASSED                                                                    [ 50%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_tablero_reintenta_el_primer_cfp_si_ambos_jugadores_tardan PASSED                                                   [ 60%]
tests/test_protocolo_partida.py::TestPartidaTablero::test_partida_completa_entre_agentes_reales PASSED                                                                       [ 70%]
tests/test_protocolo_partida.py::TestPartidaJugador::test_jugador_propone_su_jugada_con_move PASSED                                                                          [ 80%]
tests/test_protocolo_partida.py::TestPartidaJugador::test_jugador_informa_el_resultado_del_turno PASSED                                                                      [ 90%]
tests/test_protocolo_partida.py::TestPartidaJugador::test_la_partida_del_jugador_no_termina_en_aborto PASSED                                                                 [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Protocolo partida          │          10 │           0 │           0 │          10 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │          10 │           0 │           0 │          10 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 10 test(s) correctos, 0 omitido(s), 0 incidencias.
=============================================================================== 10 passed in 44.81s ===============================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_protocolo_registro.py -v
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 9 items                                                                                                                                                                  

tests/test_protocolo_registro.py::TestRegistroJugador::test_jugador_envia_solicitud_join_directa_al_tablero PASSED                                                           [ 11%]
tests/test_protocolo_registro.py::TestRegistroJugador::test_jugador_completa_la_inscripcion_tras_join_accepted PASSED                                                        [ 22%]
tests/test_protocolo_registro.py::TestRegistroJugador::test_jugador_se_detiene_si_el_tablero_lo_rechaza PASSED                                                               [ 33%]
tests/test_protocolo_registro.py::TestRegistroJugador::test_jugador_se_detiene_si_no_llega_rival PASSED                                                                      [ 44%]
tests/test_protocolo_registro.py::TestRegistroJugador::test_jugador_intenta_mas_de_una_inscripcion PASSED                                                                    [ 55%]
tests/test_protocolo_registro.py::TestRegistroTablero::test_tablero_acepta_la_inscripcion_con_join_accepted PASSED                                                           [ 66%]
tests/test_protocolo_registro.py::TestRegistroTablero::test_tablero_asigna_x_al_primero_y_o_al_segundo PASSED                                                                [ 77%]
tests/test_protocolo_registro.py::TestRegistroTablero::test_tablero_rechaza_un_tercer_jugador_por_equidad XFAIL (Prueba voluntaria: depende del descarte por equidad del...) [ 88%]
tests/test_protocolo_registro.py::TestRegistroTablero::test_tablero_avisa_con_join_timeout_si_falta_rival PASSED                                                             [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Protocolo registro         │           8 │           0 │           1 │           9 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │           8 │           0 │           1 │           9 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 8 test(s) correctos, 1 omitido(s), 0 incidencias.
-------------------------------------------------------------------------- Detalle de los tests omitidos --------------------------------------------------------------------------
[XFAIL] tests/test_protocolo_registro.py::TestRegistroTablero::test_tablero_rechaza_un_tercer_jugador_por_equidad
        Verifica: El tablero rechaza al tercer jugador en condición de carrera.
        → Prueba voluntaria: depende del descarte por equidad del gestor de inscripciones (sección 4.6 del diseño). Verifica que, cuando dos solicitudes compiten por la última plaza, la no elegida recibe REF...
          • La omisión no es un fallo de la rama: el test no se ha ejecutado porque una precondición declarada no se cumple en este entorno. El motivo (línea anterior) indica cuál.
          • Si la precondición es un servidor XMPP, revisar la sección de tests de integración de tests/README.md; si es un nivel de estrategia opcional, revisar alumno.niveles_estrategia en config/config.yaml.
========================================================================== 8 passed, 1 xfailed in 21.40s ==========================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> pytest .\tests\test_sonda_supervisor.py -v  
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0 -- C:\Users\Jesús\PycharmProjects\tictactoe-nivel1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jesús\PycharmProjects\tictactoe-nivel1
configfile: pytest.ini
plugins: aiohttp-1.1.1, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 6 items                                                                                                                                                                  

tests/test_sonda_supervisor.py::TestComprobarSupervisorActivo::test_devuelve_true_cuando_disco_responde PASSED                                                               [ 16%]
tests/test_sonda_supervisor.py::TestComprobarSupervisorActivo::test_extrae_condicion_y_texto_del_servidor PASSED                                                             [ 33%]
tests/test_sonda_supervisor.py::TestComprobarSupervisorActivo::test_informa_de_la_ausencia_de_respuesta PASSED                                                               [ 50%]
tests/test_sonda_supervisor.py::TestComprobarSupervisorActivo::test_no_propaga_el_fallo_de_stop PASSED                                                                       [ 66%]
tests/test_sonda_supervisor.py::TestSondaIntegradaEnMain::test_aborta_si_supervisor_no_esta_activo PASSED                                                                    [ 83%]
tests/test_sonda_supervisor.py::TestSondaIntegradaEnMain::test_no_se_lanza_fuera_del_modo_examen PASSED                                                                      [100%]

========================================================== Tabla resumen de la serie de validación de la rama de examen ===========================================================
┌────────────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Bloque de tests            │   Correctos │  Incidencia │    Omitidos │       Total │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Sonda supervisor           │           6 │           0 │           0 │           6 │
├────────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ TOTAL                      │           6 │           0 │           0 │           6 │
└────────────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
Veredicto: OK — 6 test(s) correctos, 0 omitido(s), 0 incidencias.
================================================================================ 6 passed in 0.74s ================================================================================
(.venv) PS C:\Users\Jesús\PycharmProjects\tictactoe-nivel1> 
```

