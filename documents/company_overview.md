# IberiaNova HealthTech - Overview

> Documento interno de overview corporativo basado en la Junta Directiva del 16/02/2026. [web:16][web:20]

---

## 1. Identidad de la compañía

**Nombre legal:** IberiaNova HealthTech, S.L.  
**Sede:** Madrid (España)  
**Sector:** HealthTech / SaaS clínico B2B  
**Modelo de negocio:** Plataforma SaaS para clínicas y aseguradoras con módulos de IA aplicada a soporte clínico y gestión operativa. [web:22][web:28]

**Misión (propuesta):**  
Facilitar decisiones clínicas y operativas más seguras y eficientes mediante IA trazable, centrada en el profesional sanitario y alineada con la normativa europea de protección de datos. [web:22][web:25]

**Clientes objetivo principales:**

- Clínicas y grupos hospitalarios.
- Aseguradoras de salud.
- Proveedores de servicios clínicos especializados. [web:22][web:28]

---

## 2. Problema y oportunidad

Los proveedores sanitarios y las aseguradoras se enfrentan a tres retos estructurales:

- Sobrecarga asistencial y tiempo limitado por paciente.
- Fragmentación documental (HIS antiguos, protocolos dispersos, múltiples sistemas).
- Riesgo regulatorio y reputacional en el uso de IA clínica sin control de fuentes ni trazabilidad. [web:22][web:28]

A nivel europeo, el crecimiento del gasto sanitario y la presión por resultados obligan a:

- Mejorar la eficiencia operativa (no-shows, tiempos de respuesta, coordinación).
- Incrementar la calidad y consistencia de las decisiones clínicas.
- Asegurar cumplimiento GDPR y requisitos de IA en salud. [web:22][web:23]

---

## 3. Propuesta de valor

IberiaNova HealthTech ofrece una plataforma SaaS B2B con módulos de IA clínica explicable, enfocada en:

- **Reducción de no-show y mejora de eficiencia** en clínicas a través de workflows y recordatorios inteligentes.
- **Optimización de siniestralidad** en aseguradoras mediante mejor soporte a decisiones y homogeneización de criterios.
- **Cumplimiento normativo** reforzado (GDPR, gestión de datos de salud, control de subprocesadores, modo EU-only). [web:22][web:23]

Puntos diferenciales:

- RAG con citación controlada y configurable por rol (usuarios clínicos vs pacientes).
- Arquitectura de búsqueda híbrida (vector + BM25) optimizada para contenido clínico.
- Enfoque “compliance-first”: DR planificado, ciberseguridad reforzada, modo EU-only contractual. [web:23][web:27]

---

## 4. Producto y roadmap

### 4.1 Módulos actuales

- Motor de recomendación nutricional (v1 en producción, v2 en desarrollo).
- Módulo de soporte clínico basado en IA (en transición hacia RAG).
- Panel de control de KPIs operativos (MRR, churn, margen, run-rate, costes cloud).

### 4.2 Roadmap 2026 (aprobado en Junta)

1. **Motor de recomendación nutricional v2**
   - Mejora de personalización por paciente y patología.
   - Métricas: adopción por clínicos, impacto en adherencia.

2. **Módulo de “resumen clínico” con RAG**
   - Fuentes autorizadas: guías internas, protocolos por especialidad, documentación del cliente.
   - Política de citación:
     - Usuarios clínicos: citas visibles por defecto.
     - Pacientes: mensaje agregado (“basado en tu plan y tu historial”) con opción a ver fuentes.
   - Registro de prompts y respuestas con retención de 90 días; anonimización acelerada para datos especialmente sensibles.

3. **Auditoría de trazabilidad y explicabilidad**
   - Registro de decisiones y fuentes usadas por el modelo.
   - Soporte a auditorías internas y regulatorias.

4. **Migración de búsqueda a arquitectura híbrida**
   - Combinación de índice vectorial y BM25.
   - Objetivo: mejorar precisión percibida, cobertura documental y tiempos de respuesta.

**Hito solicitado:**

- Informe de métricas del módulo RAG (precisión percibida, tasa de alucinación, cobertura documental, tiempos de respuesta) en la próxima Junta.

---

## 5. Modelo de negocio y KPIs

### 5.1 Modelo de ingresos

- SaaS B2B por suscripción (clínicas, grupos, aseguradoras).
- Facturación prioritaria con ciclo de cobro trimestral adelantado.
- Tarifa plana de cumplimiento para cuentas enterprise (modo EU-only, subprocesadores controlados, auditoría). [web:22][web:28]

Ingresos complementarios potenciales:

- Servicios profesionales de integración (HIS antiguos, conectores mínimos).
- Proyectos de implantación y formación avanzada.

### 5.2 KPIs clave (corte enero 2026)

- MRR: €312,400 (+6.1% vs diciembre).
- Churn neto: 1.4%.
- Margen bruto: 71%.
- Burn mensual: €265,000.
- Runway estimado: 8.3 meses.
- Caja actual: €2.2M.

Indicadores comerciales y de pipeline:

- 19 oportunidades B2B activas.
- 6 en fase legal.
- Objetivo Q1: cerrar €420,000 de ARR adicional.
- Foco en proyectos “Atlas” y “Brújula”.

Indicadores operativos/tecnológicos:

- Incremento puntual de gasto cloud (+€18,700) por sobreuso de GPU en experimentos de embeddings.
- Políticas aprobadas:
  - Cap semanal de gasto GPU; aprobación previa de Finanzas para pruebas >€5,000.
  - MFA obligatorio para accesos administrativos y simulacro de continuidad de negocio.

---

## 6. Ciberseguridad, datos y cumplimiento

### 6.1 Ciberseguridad y continuidad de negocio

Situación reciente:

- 0 brechas confirmadas.
- 3 alertas de credenciales filtradas en repositorio antiguo, mitigadas con rotación de secretos.

Medidas aprobadas:

- MFA obligatorio para accesos administrativos.
- Rotación trimestral de credenciales y revisión de permisos.
- Device posture para equipos remotos.
- Simulacro de continuidad de negocio (DR) según Anexo C.

### 6.2 Protección de datos y GDPR

Estado actual:

- Registro de Actividades de Tratamiento actualizado.
- DPA estándar revisado.
- Pendiente: adenda con proveedor de analítica (plazo 29/02/2026).

Requisitos de clientes:

- Alojamiento de datos exclusivamente en la UE.
- Evitar transferencias internacionales de datos de salud.

Respuesta de producto/legal:

- Uso de región Frankfurt y backups en París, con control de accesos de soporte.
- Creación de un modo EU-only contractual con:
  - Lista cerrada de subprocesadores.
  - Auditoría anual.
  - Tarifa de cumplimiento de €750/mes para cuentas enterprise.

---

## 7. Equipo directivo y gobierno

### 7.1 Consejo y roles clave

- **Presidente:** Javier Santamaría.
- **CEO:** Marta Ríos.
- **CFO:** Andrés Vidal.
- **COO:** Nuria Beltrán.
- **CTO:** Pablo Echeverría.
- **Consejera independiente:** Camila Torres.
- **Consejero:** Héctor Lasa.
- **Secretaria (no consejera):** Laura Prieto.
- **Directora Legal (invitada):** Silvia Mora.

### 7.2 Personas y compensación

Nuevas contrataciones propuestas:

- Ingeniero de Datos senior (aprobada).
- Account Manager para aseguradoras (condicionada al cierre del proyecto Atlas antes del 31/03/2026).

Esquema de bonus:

- Variable trimestral para ventas (hasta 12%).
- Ingeniería: ligado a disponibilidad 99.9% y reducción de coste cloud por consulta.
- OKR mixto: coste por respuesta, latencia p95, tasa de correcciones clínicas <0.8%.

---

## 8. Estrategia comercial 2026

Prioridades:

- Cierre de €420,000 de ARR adicional en Q1.
- Priorización de acuerdos con cobro trimestral adelantado.
- Segmentación del pitch comercial:
  - Clínicas: énfasis en reducción de no-show y eficiencia.
  - Aseguradoras: control de siniestralidad y coherencia de criterios.

Acciones aprobadas:

- Elaborar playbook de objeciones por sector (COO, fecha límite 01/03/2026).
- Ofrecer conector mínimo en 2 semanas para HIS antiguos, con alcance acotado, para no bloquear cierres.

---

## 9. Financiación y estructura de capital

Objetivo: extender el runway a 12–14 meses.

### 9.1 Opciones analizadas

- **Opción A – Puente convertible (€1.5M):**
  - Descuento: 15%.
  - Cap: €12M.

- **Opción B – Deuda venture (€1.0M):**
  - Interés: 11.5% anual.
  - 6 meses de carencia.
  - Con warrants.

Conclusiones de la Junta:

- Priorizar exploración del convertible con inversores actuales.
- Mantener abierta la opción de deuda, solicitando sensibilidad de caja si Q2 no cumple plan.
- Autorización a CEO y CFO a negociar, sin firma final sin aprobación de la Junta; mantener data room actualizada (Anexo D).

---

## 10. Posicionamiento de marca y mensajes públicos

Riesgo identificado:

- El término “IA clínica” puede interpretarse como dispositivo médico o promesa diagnóstica.

Decisiones de posicionamiento:

- Evitar claims diagnósticos.
- Usar “asistencia” y “soporte a profesionales” como eje de mensaje.
- Incluir disclaimers claros.
- El modelo no debe sugerir medicación, salvo reproducción literal de protocolos internos validados.

Acción acordada:

- Actualizar web y materiales comerciales antes del 05/03/2026 (Responsable: Legal/CEO).

---

## 11. Resumen ejecutivo de acuerdos clave

1. **Control de gasto GPU:** Cap semanal y aprobación de Finanzas para pruebas >€5,000.
2. **Ejecución comercial:** Playbook por sector y priorización de deals con cobro trimestral adelantado.
3. **Roadmap de producto (RAG y explicabilidad):** Citas visibles para clínicos en Q1, opción “ver fuentes” para pacientes e informe de métricas en próxima Junta.
4. **Seguridad y continuidad:** MFA obligatorio, rotación de secretos y simulacro de DR.
5. **Cumplimiento GDPR y modo EU-only:** Contrato específico, lista cerrada de subprocesadores, auditoría anual y tarifa de cumplimiento.
6. **Personas:** Contratación de Ingeniero de Datos; Account Manager condicionado al cierre de Atlas.
7. **Financiación:** Mandato a CEO/CFO para negociar puente convertible y/o deuda venture, sin firma sin nueva aprobación.
8. **Marketing y claims:** Revisión de mensajes de “IA clínica” y actualización de web y materiales.

---

## 12. Metadatos del documento

- **Tipo:** Overview corporativo interno / base para one-pager e investor deck. [web:22][web:28]
- **Fuente principal:** Acta de Junta Directiva de IberiaNova HealthTech, S.L. (16/02/2026).
- **Versión:** 0.1 (borrador para revisión por CEO, CFO, COO, CTO y Legal).
- **Próximos pasos:**
  - Validar mensajes de producto y cumplimiento.
  - Integrar secciones de mercado, competencia y casos de éxito antes de uso externo.
