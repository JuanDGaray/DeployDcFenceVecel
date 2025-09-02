# Dashboard de Proyectos Completados - Administradores

## Descripción

Este módulo proporciona una vista administrativa completa para visualizar y analizar todos los proyectos terminados en el sistema. Está diseñado exclusivamente para usuarios con permisos de administrador.

## Características Principales

### 🔐 Control de Acceso
- **Acceso Restringido**: Solo usuarios con `is_superuser=True` o `is_staff=True`
- **Verificación de Permisos**: Decorador `@user_passes_test(is_admin)` en todas las vistas

### 📊 Organización de Datos
- **Por Año y Mes**: Los proyectos se organizan cronológicamente por período de finalización
- **Totales Agregados**: Cálculos automáticos de costos y utilidades por período
- **Estadísticas Generales**: Resumen de todos los proyectos completados

### 💰 Información Financiera
- **Costo Presupuestado**: Basado en el presupuesto aprobado del proyecto
- **Costo Real**: Costo actual registrado en el sistema
- **Utilidad**: Diferencia entre propuestas aprobadas y costo real
- **Margen de Utilidad**: Porcentaje de utilidad sobre el total de propuestas

### 📱 Funcionalidades AJAX
- **Carga Dinámica**: Detalles del proyecto se cargan sin recargar la página
- **Modal Responsivo**: Información detallada en ventana emergente
- **Exportación de Datos**: Descarga de información en formato CSV

## Estructura de Archivos

```
customer/
├── views/
│   └── admin_views.py          # Vistas principales del dashboard
├── templatetags/
│   └── admin_filters.py        # Filtros personalizados para templates
├── urls.py                     # URLs del dashboard
└── models.py                   # Modelos de datos utilizados

templates/
└── admin/
    └── completed_projects_dashboard.html  # Template principal
```

## URLs Disponibles

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/customer/admin/completed-projects/` | `completed_projects_dashboard` | Dashboard principal |
| `/customer/admin/project-details/<id>/` | `get_project_details_ajax` | Detalles AJAX del proyecto |
| `/customer/admin/export-completed-projects/` | `export_completed_projects_data` | Exportación de datos |

## Modelos Utilizados

### Project
- **Estado**: Filtrado por `status='completed'`
- **Fechas**: Organización por `end_date`
- **Relaciones**: Cliente, asesor de ventas, gerente de proyecto

### BudgetEstimate
- **Versiones**: Múltiples versiones de presupuesto por proyecto
- **Estados**: Filtrado por `status__in=['completed', 'billed']`
- **Cálculos**: Costo proyectado, valor de ganancia, valor total

### ProposalProjects
- **Estado**: Solo propuestas aprobadas (`status='approved'`)
- **Montos**: Total de propuesta, monto facturado, monto restante

### InvoiceProjects
- **Información**: Subtotal, impuestos, retención, total factura
- **Pagos**: Total pagado y estado de la factura

### RealCostProject
- **Costos Reales**: Elementos de costo y totales
- **Evidencia**: URLs de documentos de respaldo

## Funciones Principales

### `calculate_project_totals(project)`
Calcula los totales financieros de un proyecto:
- Costo presupuestado
- Costo real
- Total de propuestas
- Total facturado
- Utilidad y margen

### `get_detailed_project_info(project)`
Obtiene información completa del proyecto para el modal:
- Información básica del proyecto
- Historial de presupuestos
- Propuestas aprobadas
- Facturas emitidas
- Costos reales registrados

### `export_completed_projects_data()`
Exporta todos los datos en formato JSON para conversión a CSV.

## Filtros de Template

### `get_item(dictionary, key)`
Accede a elementos de diccionarios anidados.

### `month_name(month_number)`
Convierte números de mes a nombres en español.

### `format_currency(value)`
Formatea valores como moneda con símbolo $.

### `profit_class(value)`
Asigna clases CSS según el valor de utilidad (positiva/negativa/neutral).

## Seguridad

### Verificación de Permisos
```python
def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def completed_projects_dashboard(request):
    # Solo accesible para administradores
```

### Filtrado de Datos
- Proyectos solo con estado 'completed'
- Presupuestos con estados válidos
- Propuestas solo aprobadas

## Uso del Dashboard

### 1. Acceso
- Navegar a `/customer/admin/completed-projects/`
- Verificar permisos de administrador

### 2. Navegación
- **Vista General**: Estadísticas totales en la parte superior
- **Por Período**: Organización por año y mes
- **Proyectos**: Lista detallada con información financiera

### 3. Detalles del Proyecto
- Hacer clic en "Ver Detalles" en cualquier proyecto
- Modal con información completa
- Carga AJAX para mejor rendimiento

### 4. Exportación
- Botón "Exportar Datos" en la parte superior
- Descarga automática en formato CSV
- Incluye todos los proyectos completados

## Personalización

### Colores y Estilos
- Utilidad positiva: Verde (`#28a745`)
- Utilidad negativa: Rojo (`#dc3545`)
- Utilidad neutral: Gris (`#6c757d`)

### Responsive Design
- Grid adaptativo para diferentes tamaños de pantalla
- Modal optimizado para dispositivos móviles
- Navegación táctil en dispositivos móviles

## Mantenimiento

### Actualizaciones de Datos
- Los datos se actualizan en tiempo real
- No requiere reinicio del servidor
- Cálculos automáticos de totales

### Logs y Monitoreo
- Todas las acciones se registran en el sistema
- Errores capturados y manejados apropiadamente
- Respuestas JSON consistentes para debugging

## Dependencias

- Django 3.2+
- Bootstrap 5.3+
- Font Awesome (para iconos)
- JavaScript ES6+ para funcionalidades AJAX

## Notas de Implementación

- **Performance**: Uso de `select_related()` para optimizar consultas
- **Escalabilidad**: Paginación automática para grandes volúmenes de datos
- **Mantenibilidad**: Código modular y bien documentado
- **Extensibilidad**: Fácil agregar nuevas métricas o filtros

