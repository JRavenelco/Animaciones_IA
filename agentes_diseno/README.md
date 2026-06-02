# Sistema de Agentes para el Área de Diseño (CEROC - Hangar)

Este directorio contiene la estructura de guías, flujos de trabajo e instrucciones diseñadas para orientar a los **Agentes de Inteligencia Artificial** en la ejecución de tareas de comunicación, diseño gráfico y producción audiovisual, alineadas con la **Política de Tiempos del Hangar (CECRITICC)**.

## Estructura del Árbol de Instrucciones

```
agentes_diseno/
├── README.md                          # Instrucciones principales y modo de uso del sistema.
├── politica_tiempos.md                # Base de datos de tiempos (OnTime, GAP, OverTime) y dependencias.
└── workflows/                         # Guías paso a paso para la ejecución de tareas por concepto:
    ├── workflow_cartel_flyer.md       # Carteles, Flyers, Volantes y Material de Difusión.
    ├── workflow_redes_sociales.md     # Publicaciones, Stories, Infografías y Reels.
    ├── workflow_identidad_logotipo.md # Logotipos, Identidad Corporativa y Manuales de Identidad.
    └── workflow_audiovisual.md        # Videos, Animaciones, Filtros y Postproducción.
```

---

## Instrucciones Generales para Nuevos Agentes

Cualquier agente que sea asignado a una tarea de diseño en este repositorio debe seguir estos pasos en orden:

1.  **Consulta de Viabilidad:** Leer [`politica_tiempos.md`](politica_tiempos.md) y calcular el número de días hábiles entre la fecha actual y la fecha de entrega del proyecto. Determinar si la tarea califica como **OnTime**, **GAP** o **Over Time**.
2.  **Relevamiento de Requisitos:** Acceder al flujo de trabajo correspondiente dentro de la carpeta `workflows/` (ej. para un cartel, usar [`workflows/workflow_cartel_flyer.md`](workflows/workflow_cartel_flyer.md)) y validar que se cuenta con toda la información de entrada requerida antes de comenzar la producción.
3.  **Generación de Entregables:** Ejecutar la tarea técnica según las directrices y las especificaciones de resolución (300 DPI para impresión, 1920x1080 px para video, formatos editables `.ai`, etc.).
4.  **Lista de Verificación de Calidad:** Pasar por la lista de validación definida en el flujo de trabajo antes de notificar la entrega.
5.  **Entrega y Registro:** Subir los archivos finales al directorio designado, registrar la fecha de entrega y documentar si se cumplió el tiempo comprometido.
