import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# CONFIGURACIÓN
INPUT_CSV = '/home/mataangel53/Descargas/METADATOS_COATLICUE/compranet_historico(1).csv'
OUTPUT_REPORT = 'REPORTE_FORENSE_CONTABLE.txt'

def analyze_benford(series):
    """Analiza el primer dígito de los montos para detectar manipulación."""
    counts = series.astype(str).str[0].value_counts(normalize=True).sort_index()
    # Ley de Benford teórica
    benford = pd.Series({str(d): math.log10(1 + 1/d) for d in range(1, 10)})
    
    deviations = {}
    print("\n[1] ANÁLISIS DE LEY DE BENFORD (Detección de Datos Inventados)")
    print("Dígito | Real (Tu Data) | Teórico (Benford) | Desviación")
    print("-" * 55)
    
    max_dev = 0
    digit_max_dev = 0
    
    for d in range(1, 10):
        d_str = str(d)
        real = counts.get(d_str, 0)
        theory = benford[d_str]
        diff = abs(real - theory)
        if diff > max_dev:
            max_dev = diff
            digit_max_dev = d
        
        print(f"   {d}   |     {real:.1%}     |      {theory:.1%}      |   {diff:.1%}")
        
    veredicto = "NATURAL"
    if max_dev > 0.05: veredicto = "SOSPECHOSO (Posible manipulación humana)"
    if max_dev > 0.10: veredicto = "ALTAMENTE IRREGULAR (Intervención manual probable)"
    
    print(f"\n>> VEREDICTO BENFORD: {veredicto}")
    print(f">> La mayor anomalía está en contratos que empiezan con el dígito: {digit_max_dev}")
    return veredicto

def find_structuring(df):
    """Busca fragmentación de contratos (Smurfing/Pituféo)."""
    print("\n[2] ANÁLISIS DE ESTRUCTURACIÓN (PITUFÉO)")
    print("Buscando proveedores con múltiples contratos pequeños el mismo día...")
    
    # Agrupar por Proveedor y Fecha
    # Asumimos que 'importe' ya es numérico y 'fecha_inicio' es datetime
    grouped = df.groupby(['proveedor', 'fecha_inicio']).agg(
        num_contratos=('importe', 'count'),
        monto_total=('importe', 'sum'),
        monto_promedio=('importe', 'mean')
    ).reset_index()
    
    # Filtrar: Más de 5 contratos en un día, pero monto promedio bajo (ej. < 100k)
    suspicious = grouped[
        (grouped['num_contratos'] > 5) & 
        (grouped['monto_total'] > 1000000) # Acumulado millonario
    ].sort_values(by='num_contratos', ascending=False).head(10)
    
    if not suspicious.empty:
        print(f"!! SE DETECTARON {len(suspicious)} CASOS DE POSIBLE FRAGMENTACIÓN !!")
        for idx, row in suspicious.iterrows():
            print(f"   > Proveedor: {str(row['proveedor'])[:40]}...")
            print(f"     Fecha: {row['fecha_inicio']} | Contratos: {row['num_contratos']} | Total: ${row['monto_total']:,.2f}")
    else:
        print("   No se detectó estructuración masiva evidente en el Top 10.")

def check_round_numbers(series):
    """Busca exceso de montos redondos."""
    print("\n[3] ANÁLISIS DE MONTOS REDONDOS (Cifras Exactas)")
    # Convertir a entero y ver si es igual al flotante (ej. 5000.00 == 5000)
    # Y que sea múltiplo de 10,000
    round_counts = series[(series % 10000 == 0) & (series > 0)]
    percentage = len(round_counts) / len(series)
    
    print(f"   Contratos con montos exactos (múltiplos de $10,000): {len(round_counts)}")
    print(f"   Porcentaje del total: {percentage:.2%}")
    
    if percentage > 0.05: # Umbral arbitrario de 5%
        print(">> ALERTA: Exceso de números redondos. Inusual en contabilidad real.")
    else:
        print(">> NORMAL: Proporción de números redondos dentro de lo esperado.")

# --- EJECUCIÓN PRINCIPAL ---
print("Cargando matriz de datos (esto tomará unos segundos)...")
# Leemos columnas clave solamente para ahorrar RAM
cols = ['importe', 'proveedor', 'fecha_inicio']
try:
    df = pd.read_csv(INPUT_CSV, usecols=lambda c: c.lower() in cols or c in ['IMPORTE_CONTRATO', 'PROVEEDOR_CONTRATISTA', 'FECHA_INICIO'], low_memory=False)
    
    # Normalizar nombres de columnas
    df.columns = df.columns.str.lower()
    mapping = {'importe_contrato': 'importe', 'proveedor_contratista': 'proveedor'}
    df.rename(columns=mapping, inplace=True)
    
    # Limpieza rápida
    df['importe'] = pd.to_numeric(df['importe'], errors='coerce')
    df.dropna(subset=['importe'], inplace=True)
    df = df[df['importe'] > 100] # Ignoramos micro-pagos irrelevantes
    
    print(f"Datos listos. Analizando {len(df):,} transacciones contables.")
    
    # Ejecutar batería de pruebas
    analyze_benford(df['importe'])
    check_round_numbers(df['importe'])
    find_structuring(df)
    
except Exception as e:
    print(f"Error crítico: {e}")
    print("Verifica los nombres de las columnas en tu CSV.")

