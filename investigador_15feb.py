import pandas as pd

# CONFIGURACIÓN
INPUT_CSV = '/home/mataangel53/Descargas/METADATOS_COATLICUE/compranet_historico(1).csv'
TARGET_DATE = '2017-02-15' # La fecha de la anomalía

print(f"[*] Iniciando Investigación Profunda para la fecha: {TARGET_DATE}...")

try:
    # Leemos todo el archivo
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    
    # Normalizar columnas
    df.columns = df.columns.str.lower().str.strip()
    rename_map = {
        'descripcion_contrato': 'descripcion',
        'fecha_inicio': 'fecha'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # Filtrar por fecha
    df_feb15 = df[df['fecha'].astype(str).str.contains(TARGET_DATE, na=False)].copy()
    
    if df_feb15.empty:
        print("Error: No se encontraron registros con esa fecha exacta.")
        exit()

    print(f"\n[RESULTADOS] Transacciones detectadas el {TARGET_DATE}: {len(df_feb15)}")
    
    # Limpieza de datos para el análisis
    df_feb15['importe'] = pd.to_numeric(df_feb15['importe'], errors='coerce')
    df_feb15.dropna(subset=['importe'], inplace=True)

    print("\n--- [1] ¿QUÉ COMPRARON? (Descripciones más comunes) ---")
    # Limpiamos y contamos las descripciones
    descriptions = df_feb15['descripcion'].dropna().astype(str)
    print(descriptions.value_counts().head(5))
    
    total_dia = df_feb15['importe'].sum()
    print(f"\n--- [2] MONTO TOTAL DEL DÍA: ${total_dia:,.2f} ---")
    
    print("\n--- [3] DETALLE DE PROVEEDORES SOSPECHOSOS ---")
    top_prov = df_feb15['proveedor'].dropna().value_counts().head(10)
    for prov, count in top_prov.items():
        monto_prov = df_feb15[df_feb15['proveedor'] == prov]['importe'].sum()
        print(f"> {prov[:50]}... | Contratos: {count} | Total: ${monto_prov:,.2f}")
        
    # Guardar evidencia
    output_file = "EVIDENCIA_ANOMALIA_15FEB2017.csv"
    df_feb15.to_csv(output_file, index=False)
    print(f"\n[!] Evidencia detallada guardada en: {output_file}")

except Exception as e:
    print(f"Error crítico: {e}")