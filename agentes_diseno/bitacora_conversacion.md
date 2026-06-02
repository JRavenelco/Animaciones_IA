# Bitácora de Conversación y Contexto de Proyecto (2 de junio de 2026)

Esta bitácora registra la conversación inicial y las decisiones tomadas que llevaron a la creación de este sistema de instrucciones de diseño. Sirve como contexto histórico para cualquier agente de IA que trabaje en este repositorio.

---

## 1. Solicitud Inicial del Usuario
El usuario solicitó:
1.  Crear una carpeta llamada `reglas de medio hangar`.
2.  Copiar a dicha carpeta el archivo PDF `Formato de tiempos de realización en producción creativa_CECRITICC 2023.pdf` ubicado en su directorio local de *Descargas*.
3.  Analizar el PDF para extraer las reglas y tiempos de producción creativa del Hangar.
4.  Generar un **caso práctico** basado en un correo recibido de la Coordinación de CEROC solicitando la difusión de su participación en los **Foros Regionales del COMIE 2026** (fecha de participación: 16 de junio de 2026).
5.  Crear una estructura y árbol de instrucciones en el repositorio de Git para guiar a futuros agentes en la realización de tareas del área de diseño.

---

## 2. Desarrollo del Caso Práctico: Foros COMIE 2026

Se calculó la viabilidad del proyecto con base en **9-10 días hábiles** disponibles (desde el análisis el 2 de junio hasta el inicio del evento el 15 de junio y la participación de CEROC el 16 de junio):

*   **Boletín de Prensa:** Viabilidad **ALTA** (OnTime = 2 días).
*   **Diseño de Cartel / Post:** Viabilidad **ALTA** (OnTime = 5 días, GAP = 10 días).
*   **Difusión en Redes UAQ Institucionales:** Viabilidad **MEDIA/BAJA** (OnTime = 10 días). Requiere inicio urgente en modo GAP.
*   **Reels/Video corto:** Viabilidad **MEDIA** (OnTime = 8 días). Requiere insumos completos inmediatos.

Se generaron borradores de difusión listos para usar (un post para redes sociales y una nota informativa de prensa), los cuales se detallan en [`reglas de medio hangar/analisis_tiempos_comie.md`](../reglas%20de%20medio%20hangar/analisis_tiempos_comie.md).

---

## 3. Estructuración del Sistema de Agentes
Para automatizar y estandarizar el trabajo de diseño de futuros agentes de IA en el repositorio, se creó la carpeta [`agentes_diseno`](./README.md) con el siguiente árbol de archivos:

*   [`README.md`](./README.md): Punto de entrada y guía general.
*   [`politica_tiempos.md`](./politica_tiempos.md): Tabla completa con los 26 conceptos creativos y sus plazos OnTime, GAP y OverTime.
*   [`workflows/workflow_cartel_flyer.md`](./workflows/workflow_cartel_flyer.md): Instrucciones específicas para carteles y folletos (DPI, CMYK, códigos QR, etc.).
*   [`workflows/workflow_redes_sociales.md`](./workflows/workflow_redes_sociales.md): Dimensiones, safe zones y reglas de subtitulado para posts y reels.
*   [`workflows/workflow_identidad_logotipo.md`](./workflows/workflow_identidad_logotipo.md): Proceso de diseño vectorial, manuales de marca y entregables.
*   [`workflows/workflow_audiovisual.md`](./workflows/workflow_audiovisual.md): Pautas de grabación, audio, plecas institucionales y renderizado de video.
