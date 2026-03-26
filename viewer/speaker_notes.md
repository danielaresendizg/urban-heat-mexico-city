# Guion técnico de presentación (40 min) + versión corta (20 min)

## Estructura 40 minutos (alineada a `viewer/index.html`)

### 1) `#hero` (00:00-01:00)
- Mensaje de apertura: esta tesis analiza desigualdades térmicas en la CDMX con un pipeline multiescalar, de ciudad a calle.
- Objetivo: pasar de mapas térmicos a exposición peatonal medible y criterios técnicos verificables.

### 2) `#presentacion` (01:00-02:30)
- Perfil y enfoque: análisis espacial, clima urbano y simulación microclimática.
- Valor metodológico: integrar percepción remota, morfología urbana y red vial en un solo marco.

### 3) `#agenda` Preguntas de investigación (02:30-05:00)
- Macro: Where do daytime summer air temperatures co-locate with socially vulnerable populations?
- Meso: Which combinations of urban form/density and network configuration characterise thermal-social hotspots?
- Micro: How can micro-scale thermal stress be assessed to define passive design targets for heat reduction?

### 4) `#decision` Hipótesis y aporte (05:00-07:00)
- Hipótesis operativa: la exposición peatonal se concentra en corredores altamente integrados donde coexiste vulnerabilidad social.
- Aporte: sistema multiescalar reproducible con Tmrt, UTCI y PET para priorización espacial.

### 5) `#metodologia` (07:00-12:00)
- Fase macro: Landsat 8/9 (2014-2024), correcciones radiométricas, LST y calibración con RedMet.
- Modelo local: `Ta = 0.5540 * LST + 5.7606` (18 estaciones, 10:00-14:00).
- Fase meso: Space Matrix (FSI, GSI, L, OSR) + Space Syntax (NAIN/NACH en 500, 1000, 1500 y 5000 m).
- Fase micro: UMEP/SOLWEIG para Tmrt, UTCI y PET en 10:00, 12:00 y 14:00.

### 6) `#datos` (12:00-13:30)
- Fuentes abiertas: Landsat C2 L2, INEGI 2020, RedMet, Open Buildings, OSM/red oficial, DEM/DSM.
- Unidad de análisis: manzana (macro/meso) y corredor peatonal (micro).

### 7) `#macro` (13:30-19:00)
- Resultado clave: 32% de manzanas supera 26 C y 11% supera 28 C.
- Patrón espacial: centro-oriente ~26.8 C; anomalías UHI_air > +1.5 sigma en oriente/noreste.
- Hotspots conservadores: umbral térmico + asociación social local significativa (GWR).

### 8) `#meso` (19:00-24:00)
- Mecanismo morfológico: GSI con correlación negativa con NDVI (r=-0.299) y positiva con Ta_mean (r=0.228).
- Mecanismo configuracional: zonas más calientes también más integradas (hazard 2 > hazard 1 > hazard 0 en NAIN/NACH).
- Hallazgo operativo: convergencia entre accesibilidad peatonal y exposición térmica.

### 9) `#validacion` (24:00-27:00)
- GWR mejora ajuste en 16/16 alcaldías y mejora Moran p en 11/16 frente a OLS.
- Límites: autocorrelación residual, calibración centrada en horario diurno, sin calor antropogénico explícito en SOLWEIG, variables sociales como proxies.

### 10) `#visor` (27:00-29:00)
- Explicar que el visor es la capa de trazabilidad espacial del pipeline (no sustituye el análisis estadístico).
- Mostrar cómo cruzar calor, vulnerabilidad, morfología y red en un mismo entorno.

### 11) `#micro` (29:00-35:00)
- Umbrales: UTCI >= 32 C (estrés fuerte), UTCI >= 38 C (muy fuerte), PET > 41 C (extremo).
- Zona 1 (Hospital): régimen 26-28 C, sensibilidad en 65+ y baja escolaridad; PET extremo en puntos críticos.
- Zona 2 (AICM): transición hot26 a hot28; UTCI ~34-35, PET >41 en horas críticas.
- Zona 3 (Basílica): régimen extremo >=28 C; adultos mayores como grupo dominante; máximos PET ~43-44 C.
- Resultado transversal: picos en corredores de alta integración.

### 12) `#sintesis` (35:00-37:00)
- Gradiente de riesgo: Zona 1 (moderado) -> Zona 2 (transición) -> Zona 3 (extremo).
- Regla espacial: compacidad + alta integración + baja vegetación = mayor carga térmica peatonal.

### 13) `#kpi` + `#decision-costo-impacto-plazo` (37:00-39:00)
- Métricas de seguimiento: reducción de Tmrt, continuidad de sombra, distancia entre refugios, reducción de segmentos extremos.
- Énfasis técnico: medir resultados térmicos y no solo acciones ejecutadas.

### 14) `#cierre` (39:00-40:00)
- Conclusión: la desigualdad térmica en CDMX es medible, espacialmente concentrada y socialmente estructurada.
- Aporte final: puente metodológico ciudad-calle replicable con datos abiertos.

---

## Estructura corta 20 minutos

### Bloque 1 (00:00-02:00)
- Problema, objetivo y enfoque de tesis.

### Bloque 2 (02:00-04:00)
- Tres preguntas de investigación.

### Bloque 3 (04:00-07:00)
- Método y datos (pipeline + calibración LST->Ta).

### Bloque 4 (07:00-10:00)
- Hallazgos macro (32%, 11%, gradiente térmico).

### Bloque 5 (10:00-13:00)
- Hallazgos meso + validación + límites.

### Bloque 6 (13:00-17:00)
- Hallazgos micro (3 zonas, 3 horarios, umbrales UTCI/PET).

### Bloque 7 (17:00-20:00)
- Síntesis, KPIs térmicos y cierre.

---

## Preguntas técnicas esperables (Q&A)

1. ¿Por qué Ta y no solo LST?
- LST mide superficie; la exposición humana se aproxima mejor con Ta calibrada y, a escala peatonal, con Tmrt/UTCI/PET.

2. ¿GWR permite causalidad?
- No. GWR identifica heterogeneidad espacial local de asociaciones; se usa para diagnóstico y priorización espacial.

3. ¿Qué variable morfológica explica más?
- GSI, por su relación con sellado de suelo, menor NDVI y mayor Ta.

4. ¿Qué tan robusto es micro sin calor antropogénico explícito?
- Es una limitación declarada; la consistencia macro-meso-micro refuerza la robustez de patrones espaciales.

5. ¿Cuál es el mensaje operativo más fuerte?
- Los corredores más integrados también son los más expuestos: donde más se camina es donde más urge mitigar carga radiante.
