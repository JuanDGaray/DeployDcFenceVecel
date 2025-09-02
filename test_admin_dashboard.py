#!/usr/bin/env python3
"""
Script de prueba para el Dashboard de Proyectos Completados
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcfence.settings')
django.setup()

from customer.models import Project, BudgetEstimate, ProposalProjects, InvoiceProjects
from customer.views.admin_views import calculate_project_totals, get_detailed_project_info

def test_admin_functions():
    """Prueba las funciones principales del dashboard"""
    
    print("🧪 Probando funciones del Dashboard de Administradores...")
    
    # Buscar proyectos completados
    completed_projects = Project.objects.filter(status='completed')
    print(f"📊 Proyectos completados encontrados: {completed_projects.count()}")
    
    if completed_projects.exists():
        # Probar con el primer proyecto
        project = completed_projects.first()
        print(f"\n🔍 Probando con proyecto: {project.project_name}")
        
        # Probar cálculo de totales
        try:
            totals = calculate_project_totals(project)
            print(f"✅ Totales calculados correctamente:")
            print(f"   - Costo presupuestado: ${totals['budgeted_cost']:,.2f}")
            print(f"   - Costo real: ${totals['actual_cost']:,.2f}")
            print(f"   - Total propuestas: ${totals['total_proposals']:,.2f}")
            print(f"   - Utilidad: ${totals['profit']:,.2f}")
            print(f"   - Margen: {totals['profit_margin']:.1f}%")
        except Exception as e:
            print(f"❌ Error al calcular totales: {e}")
        
        # Probar obtención de detalles
        try:
            details = get_detailed_project_info(project)
            print(f"\n✅ Detalles obtenidos correctamente:")
            print(f"   - Información del proyecto: {len(details['project'])} campos")
            print(f"   - Presupuestos: {len(details['budgets'])} registros")
            print(f"   - Propuestas: {len(details['proposals'])} registros")
            print(f"   - Facturas: {len(details['invoices'])} registros")
            print(f"   - Costos reales: {len(details['real_costs'])} registros")
        except Exception as e:
            print(f"❌ Error al obtener detalles: {e}")
    
    else:
        print("⚠️  No hay proyectos completados para probar")
        print("   Sugerencia: Crear un proyecto de prueba con status='completed'")
    
    print("\n🎯 Pruebas completadas!")

def test_project_data():
    """Prueba la estructura de datos de proyectos"""
    
    print("\n📋 Verificando estructura de datos...")
    
    # Verificar estados de proyectos
    project_statuses = Project.objects.values_list('status', flat=True).distinct()
    print(f"Estados de proyecto disponibles: {list(project_statuses)}")
    
    # Verificar estados de presupuestos
    budget_statuses = BudgetEstimate.objects.values_list('status', flat=True).distinct()
    print(f"Estados de presupuesto disponibles: {list(budget_statuses)}")
    
    # Verificar estados de propuestas
    proposal_statuses = ProposalProjects.objects.values_list('status', flat=True).distinct()
    print(f"Estados de propuesta disponibles: {list(proposal_statuses)}")
    
    # Verificar estados de facturas
    invoice_statuses = InvoiceProjects.objects.values_list('status', flat=True).distinct()
    print(f"Estados de factura disponibles: {list(invoice_statuses)}")

if __name__ == '__main__':
    print("🚀 Iniciando pruebas del Dashboard de Administradores")
    print("=" * 60)
    
    try:
        test_project_data()
        test_admin_functions()
        print("\n✅ Todas las pruebas se ejecutaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Fin de las pruebas")

