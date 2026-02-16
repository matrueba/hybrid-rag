# ACTA DE JUNTA DIRECTIVA — IberiaNova HealthTech, S.L.

**Fecha:** 16 de febrero de 2026  
**Hora:** 09:00 CET  
**Lugar:** Sala A, sede central (Madrid) + Videoconferencia  
**Tipo de sesión:** Ordinaria (híbrida)

---

## Asistentes

**Presidente:** D. Javier Santamaría  
**Secretaria:** Dña. Laura Prieto (Secretaria no consejera)

**Consejeros presentes:**

- Dña. Marta Ríos (CEO)
- D. Andrés Vidal (CFO)
- Dña. Nuria Beltrán (COO)
- D. Pablo Echeverría (CTO)
- Dña. Camila Torres (Consejera independiente)
- D. Héctor Lasa (Consejero)

**Invitados:**

- Dña. Silvia Mora (Directora Legal)

---

## Orden del Día

1. Aprobación del acta anterior (20/01/2026)
2. Seguimiento de KPIs de Q1 y cierre provisional enero
3. Plan comercial 2026 (B2B clínicas y aseguradoras)
4. Hoja de ruta de producto (IA, RAG y cumplimiento)
5. Ciberseguridad y continuidad de negocio
6. Asuntos legales (GDPR, DPA, contratos)
7. Personas y compensación (bonus y contratación)
8. Financiación: extensión de runway y opción de deuda
9. Varios y ruegos/preguntas

---

## Desarrollo de la Sesión

### 1. Aprobación del Acta Anterior

La Secretaria somete a aprobación el acta de la sesión de 20/01/2026. Dña. Camila Torres solicita corregir una cifra: donde consta "CAC medio €120" debe figurar "CAC medio €128" según el dashboard adjunto de enero (Anexo B).

**Acuerdo:** Se aprueba el acta con la corrección solicitada por unanimidad (7 votos a favor).

El Presidente recuerda que los acuerdos aprobados deben reflejarse en el libro de actas antes del 28/02/2026 y solicita a Legal revisar coherencia con los contratos marco firmados en Q4.

---

### 2. Seguimiento de KPIs y Cierre Provisional Enero

D. Andrés Vidal (CFO) presenta el cierre provisional de enero:

**Métricas principales:**

- MRR: €312,400 (+6.1% vs diciembre)
- Churn neto: 1.4%
- Margen bruto: 71%
- Burn mensual: €265,000
- Runway estimado: 8.3 meses
- Caja actual: €2.2M

**Desviaciones:** Gasto cloud +€18,700 por sobreuso de GPU en experimentos de embeddings.

D. Pablo Echeverría (CTO) aclara que se ejecutaron pruebas A/B con tres configuraciones de indexado y que dos configuraciones ya se apagaron.

**Acuerdo:** Toda prueba con GPU debe tener un "cap" semanal y aprobación previa de Finanzas si supera €5,000 (Responsable: CEO/CFO, inmediato).

D. Héctor Lasa pregunta por el impacto de la subida de precios. El CFO confirma que el incremento del 3% aplicado a 42 cuentas no generó bajas, pero sí 6 solicitudes de renegociación.

---

### 3. Plan Comercial 2026

Dña. Nuria Beltrán (COO) presenta el pipeline comercial:

- 19 oportunidades activas B2B
- 6 en fase legal
- Objetivo Q1: cerrar €420,000 de ARR adicional
- Foco en dos acuerdos principales: Proyecto "Atlas" y "Brújula"

Dña. Camila Torres sugiere segmentar el pitch: para clínicas enfatizar reducción de no-show y eficiencia; para aseguradoras, control de siniestralidad.

**Acuerdo:** El equipo de ventas priorizará deals con ciclo de cobro trimestral adelantado. Se solicita un "playbook" de objeciones por sector (Responsable: COO, fecha límite: 01/03/2026).

El Presidente pregunta si el forecast contempla estacionalidad de marzo. La COO confirma que sí, pero identifica como riesgo principal la validación de integraciones con HIS antiguos.

El CTO propone ofrecer un "conector mínimo" en 2 semanas, con alcance acotado, para no bloquear cierres.

---

### 4. Hoja de Ruta de Producto

D. Pablo Echeverría (CTO) presenta la hoja de ruta:

1. Motor de recomendación nutricional versión 2
2. Módulo de "resumen clínico" con RAG
3. Auditoría de trazabilidad y explicabilidad
4. Migración de búsqueda a arquitectura híbrida (vector + BM25)

**Módulo RAG:** Requiere definir fuentes autorizadas (guías internas, protocolos por especialidad, documentación del cliente).

Dña. Silvia Mora (Legal) advierte:

- No indexar contenido de terceros sin licencia
- Documentos de clientes requieren clasificación y control de acceso estricto

Se debate el "nivel de citación". Dña. Camila quiere citas visibles para el usuario final; D. Héctor teme fricción.

**Acuerdo:** Enfoque gradual en Q1:

- Citas visibles para usuarios clínicos
- Para pacientes: mostrar "basado en tu plan y tu historial" con enlace opcional a "ver fuentes"
- Responsable: CTO, 31/03/2026

El CTO añade que se implementará registro de prompts y respuestas con retención de 90 días. Datos especialmente sensibles se anonimizarán en 24 horas.

---

### 5. Ciberseguridad y Continuidad de Negocio

D. Pablo Echeverría presenta incidentes:

- 0 brechas confirmadas
- 3 alertas de credenciales filtradas en repositorio antiguo (mitigado con rotación de secretos)

**Propuestas:**

- MFA obligatorio para accesos administrativos (antes del 22/02/2026)
- "Device posture" para equipo remoto
- Coste: €1,200/mes en licencias adicionales

El CFO pregunta por el coste. Dña. Silvia Mora recuerda que una brecha con datos de salud puede implicar sanciones relevantes y daño reputacional.

**Acuerdo:** Se aprueba por unanimidad el paquete de medidas de seguridad (MFA, rotación trimestral, revisión de permisos) y simulacro de continuidad de negocio el 15/03/2026 (Responsable: CTO).

---

### 6. Asuntos Legales

Dña. Silvia Mora informa del estado GDPR:

- Actualizado el Registro de Actividades de Tratamiento
- Revisado el DPA estándar
- Pendiente: firmar adenda con proveedor de analítica (plazo 29/02/2026)

**Solicitud de cliente:** Alojar datos exclusivamente en la UE y evitar transferencias internacionales.

El CTO confirma que actualmente se usa región Frankfurt y backups en París, pero algunos servicios de soporte podrían implicar acceso desde fuera de la UE.

**Acuerdo:** Crear un "modo EU-only" contractual con lista cerrada de subprocesadores y auditoría anual. D. Héctor propone cobrar fee adicional de 0.5% del contrato. La CEO simplifica: tarifa plana de cumplimiento de €750/mes para cuentas enterprise.

Se solicita a Legal y CFO presentar propuesta final el 25/02/2026.

---

### 7. Personas y Compensación

Dña. Nuria Beltrán propone contratar 2 perfiles:

- Ingeniero de Datos senior
- Account Manager para aseguradoras
- Coste anual total estimado: €210,000 bruto + 18% cargas

El CFO advierte que el runway bajaría a 7.5 meses sin incremento de ingresos.

**Acuerdo:**

- Contratación del Ingeniero de Datos aprobada (Responsable: COO, oferta antes del 29/02/2026)
- Account Manager: aprobación condicionada a cerrar "Atlas" antes del 31/03/2026

**Esquema de bonus:**

- Variable trimestral para ventas (hasta 12%)
- Ingeniería: ligado a disponibilidad 99.9% y reducción de coste cloud por consulta
- OKR mixto: coste por respuesta, latencia p95, tasa de correcciones clínicas <0.8%

---

### 8. Financiación

D. Andrés Vidal presenta dos opciones para extender runway a 12-14 meses:

**Opción A:** Puente convertible de €1.5M

- Descuento 15%
- Cap €12M

**Opción B:** Deuda venture de €1.0M

- Interés 11.5% anual
- 6 meses de carencia
- Warrants

El Presidente sugiere explorar primero el convertible con inversores actuales. D. Héctor prefiere deuda para minimizar dilución, pero pide sensibilidad de caja si Q2 no cumple.

**Acuerdo:** Se aprueba por mayoría (6 a favor, 1 en contra: D. Héctor) autorizar a CEO y CFO a negociar, sin firma final sin aprobación de la Junta. Se mantendrá "data room" actualizada (Anexo D: checklist).

Responsables: CEO/CFO, actualización en próxima junta.

---

### 9. Varios

Dña. Camila Torres pregunta por coherencia del mensaje público: "IA clínica" puede interpretarse como dispositivo médico.

Dña. Silvia Mora recomienda:

- Evitar claims diagnósticos
- Usar "asistencia" y "soporte a profesionales"
- Incluir disclaimers

El CTO añade que el modelo no debe sugerir medicación, salvo reproducción literal de protocolos internos validados.

**Acuerdo:** Actualizar web y materiales comerciales antes del 05/03/2026 (Responsable: Legal/CEO).

El Presidente solicita que en la próxima reunión se presente un informe de métricas del módulo RAG:

- Precisión percibida
- Tasa de alucinación detectada
- Cobertura documental
- Tiempos de respuesta

---

## Resumen de Acuerdos y Responsables

1. **Cap de gasto GPU:** Aprobación previa >€5,000 (CEO/CFO, inmediato)
2. **Playbook de ventas:** Por sector (COO, 01/03/2026)
3. **Citas visibles en RAG:** Para clínicos en Q1 (CTO, 31/03/2026)
4. **MFA obligatorio:** Y simulacro DR (CTO, 22/02/2026 y 15/03/2026)
5. **Modo EU-only:** Y propuesta de pricing (Legal/CFO, 25/02/2026)
6. **Contratación:** Ingeniero de Datos (COO, oferta antes del 29/02/2026)
7. **Negociación financiación:** (CEO/CFO, actualización en próxima junta)
8. **Revisión claims:** De marketing (Legal/CEO, 05/03/2026)

---

## Cierre

No habiendo más asuntos, se levantó la sesión a las 11:12 CET.

La Secretaria redacta el acta, que se remitirá para comentarios en 48 horas.

**Firman electrónicamente:**

- D. Javier Santamaría (Presidente)
- Dña. Laura Prieto (Secretaria)

Madrid, 16 de febrero de 2026

---

## Anexos Referenciados

- **Anexo A:** Orden del día enviado el 12/02/2026
- **Anexo B:** Dashboard de métricas enero 2026
- **Anexo C:** Plan de DR y continuidad de negocio
- **Anexo D:** Checklist de data room para financiación
