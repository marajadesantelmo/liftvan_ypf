import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Comparación de Precios Marítimos",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para cargar datos
@st.cache_data
def load_data():
    try:
        comparison_df = pd.read_csv('data/price_comparison.csv')
        no_matches_df = pd.read_csv('data/no_matches.csv')
        summary_stats = pd.read_csv('data/summary_statistics.csv', index_col=0)
        airesds_df = pd.read_csv('data/airesds_data.csv')
        fcl_df = pd.read_csv('data/fcl_data.csv')
        silver_df = pd.read_csv('data/silver_data.csv')
        
        return comparison_df, no_matches_df, summary_stats, airesds_df, fcl_df, silver_df
    except FileNotFoundError as e:
        st.error(f"Error: No se pudieron cargar los datos. Asegúrate de ejecutar comparacion.py primero. {e}")
        st.stop()

# Cargar datos
comparison_df, no_matches_df, summary_stats, airesds_df, fcl_df, silver_df = load_data()

# Título principal
st.title("🚢 Dashboard de Comparación de Precios Marítimos")
st.markdown("### Análisis comparativo de precios entre AiresDS, FCL y Silver")

# Sidebar para filtros
st.sidebar.header("🔍 Filtros")

# Filtro por proveedor
proveedores_disponibles = []
if not comparison_df.empty:
    proveedores_20 = comparison_df['best_provider_20'].dropna().unique().tolist()
    proveedores_40 = comparison_df['best_provider_40'].dropna().unique().tolist()
    proveedores_disponibles = list(set(proveedores_20 + proveedores_40))

proveedor_filter = st.sidebar.multiselect(
    "Filtrar por mejor proveedor:",
    options=proveedores_disponibles,
    default=proveedores_disponibles
)

# Filtro por rango de precios (contenedor 20')
if not comparison_df.empty and 'best_price_20' in comparison_df.columns:
    min_price_20 = comparison_df['best_price_20'].min()
    max_price_20 = comparison_df['best_price_20'].max()
    
    price_range_20 = st.sidebar.slider(
        "Rango de precios contenedor 20' (USD):",
        min_value=float(min_price_20),
        max_value=float(max_price_20),
        value=(float(min_price_20), float(max_price_20)),
        step=50.0
    )

# Filtro por diferencia de precio
if not comparison_df.empty and 'price_diff_20_pct' in comparison_df.columns:
    max_diff_pct = comparison_df['price_diff_20_pct'].max()
    
    diff_threshold = st.sidebar.slider(
        "Diferencia mínima de precio (%):",
        min_value=0.0,
        max_value=float(max_diff_pct),
        value=0.0,
        step=5.0
    )

# Filtro por número de fuentes
sources_filter = st.sidebar.selectbox(
    "Número de fuentes disponibles:",
    options=[2, 3, "Todas"],
    index=2
)

# Aplicar filtros
filtered_df = comparison_df.copy()

if not filtered_df.empty:
    # Filtrar por proveedor
    if proveedor_filter:
        mask = (filtered_df['best_provider_20'].isin(proveedor_filter)) | \
               (filtered_df['best_provider_40'].isin(proveedor_filter))
        filtered_df = filtered_df[mask]
    
    # Filtrar por rango de precios
    if 'best_price_20' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['best_price_20'] >= price_range_20[0]) &
            (filtered_df['best_price_20'] <= price_range_20[1])
        ]
    
    # Filtrar por diferencia de precio
    if 'price_diff_20_pct' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['price_diff_20_pct'] >= diff_threshold]
    
    # Filtrar por número de fuentes
    if sources_filter != "Todas":
        filtered_df = filtered_df[filtered_df['sources_available'] == sources_filter]

# Crear tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resumen Ejecutivo", 
    "💰 Comparación de Precios", 
    "📈 Análisis por Proveedor", 
    "🗺️ Destinos sin Coincidencias",
    "📋 Datos Detallados"
])

with tab1:
    st.header("📊 Resumen Ejecutivo")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_destinos = len(comparison_df) if not comparison_df.empty else 0
        st.metric("Total Destinos Comparados", total_destinos)
    
    with col2:
        destinos_sin_match = len(no_matches_df) if not no_matches_df.empty else 0
        st.metric("Destinos sin Coincidencias", destinos_sin_match)
    
    with col3:
        if not comparison_df.empty and 'price_diff_20_pct' in comparison_df.columns:
            avg_diff = comparison_df['price_diff_20_pct'].mean()
            st.metric("Diferencia Promedio (%)", f"{avg_diff:.1f}%")
        else:
            st.metric("Diferencia Promedio (%)", "N/A")
    
    with col4:
        if not comparison_df.empty and 'price_diff_20_pct' in comparison_df.columns:
            max_diff = comparison_df['price_diff_20_pct'].max()
            st.metric("Diferencia Máxima (%)", f"{max_diff:.1f}%")
        else:
            st.metric("Diferencia Máxima (%)", "N/A")
    
    # Gráfico de rendimiento por proveedor
    if not comparison_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Mejores Precios por Proveedor (Contenedor 20')")
            provider_counts_20 = comparison_df['best_provider_20'].value_counts()
            
            fig_provider_20 = px.pie(
                values=provider_counts_20.values,
                names=provider_counts_20.index,
                title="Distribución de Mejores Precios - Contenedor 20'"
            )
            fig_provider_20.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_provider_20, use_container_width=True)
        
        with col2:
            st.subheader("Mejores Precios por Proveedor (Contenedor 40')")
            provider_counts_40 = comparison_df['best_provider_40'].value_counts()
            
            fig_provider_40 = px.pie(
                values=provider_counts_40.values,
                names=provider_counts_40.index,
                title="Distribución de Mejores Precios - Contenedor 40'"
            )
            fig_provider_40.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_provider_40, use_container_width=True)

with tab2:
    st.header("💰 Comparación de Precios")
    
    if not filtered_df.empty:
        # Top 10 diferencias más grandes
        st.subheader("Top 10 Destinos con Mayores Diferencias de Precio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Contenedor 20'**")
            top_diff_20 = filtered_df.nlargest(10, 'price_diff_20_pct')[
                ['destino', 'best_price_20', 'worst_price_20', 'price_diff_20_pct', 'best_provider_20']
            ].round(2)
            top_diff_20.columns = ['Destino', 'Mejor Precio', 'Peor Precio', 'Diferencia %', 'Mejor Proveedor']
            st.dataframe(top_diff_20, use_container_width=True)
        
        with col2:
            st.write("**Contenedor 40'**")
            top_diff_40 = filtered_df.nlargest(10, 'price_diff_40_pct')[
                ['destino', 'best_price_40', 'worst_price_40', 'price_diff_40_pct', 'best_provider_40']
            ].round(2)
            top_diff_40.columns = ['Destino', 'Mejor Precio', 'Peor Precio', 'Diferencia %', 'Mejor Proveedor']
            st.dataframe(top_diff_40, use_container_width=True)
        
        # Gráfico de dispersión de precios
        st.subheader("Análisis de Dispersión de Precios")
        
        fig_scatter = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Contenedor 20\'', 'Contenedor 40\''),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Scatter plot para 20'
        fig_scatter.add_trace(
            go.Scatter(
                x=filtered_df['best_price_20'],
                y=filtered_df['price_diff_20_pct'],
                mode='markers',
                name='20\'',
                text=filtered_df['destino'],
                hovertemplate='<b>%{text}</b><br>Mejor Precio: $%{x}<br>Diferencia: %{y:.1f}%<extra></extra>',
                marker=dict(size=8, color='blue', opacity=0.6)
            ),
            row=1, col=1
        )
        
        # Scatter plot para 40'
        fig_scatter.add_trace(
            go.Scatter(
                x=filtered_df['best_price_40'],
                y=filtered_df['price_diff_40_pct'],
                mode='markers',
                name='40\'',
                text=filtered_df['destino'],
                hovertemplate='<b>%{text}</b><br>Mejor Precio: $%{x}<br>Diferencia: %{y:.1f}%<extra></extra>',
                marker=dict(size=8, color='red', opacity=0.6)
            ),
            row=1, col=2
        )
        
        fig_scatter.update_xaxes(title_text="Mejor Precio (USD)", row=1, col=1)
        fig_scatter.update_xaxes(title_text="Mejor Precio (USD)", row=1, col=2)
        fig_scatter.update_yaxes(title_text="Diferencia de Precio (%)", row=1, col=1)
        fig_scatter.update_yaxes(title_text="Diferencia de Precio (%)", row=1, col=2)
        
        fig_scatter.update_layout(
            title="Relación entre Precio Base y Diferencia Porcentual",
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    else:
        st.warning("No hay datos que mostrar con los filtros aplicados.")

with tab3:
    st.header("📈 Análisis por Proveedor")
    
    if not comparison_df.empty:
        # Comparación de precios promedio por proveedor
        st.subheader("Precios Promedio por Proveedor")
        
        # Calcular precios promedio
        avg_prices_data = []
        
        for provider in ['aires', 'fcl', 'silver']:
            col_20 = f'{provider}_20'
            col_40 = f'{provider}_40'
            
            if col_20 in comparison_df.columns and col_40 in comparison_df.columns:
                avg_20 = comparison_df[col_20].mean()
                avg_40 = comparison_df[col_40].mean()
                
                avg_prices_data.append({
                    'Proveedor': provider.capitalize(),
                    'Promedio 20\'': avg_20,
                    'Promedio 40\'': avg_40
                })
        
        if avg_prices_data:
            avg_prices_df = pd.DataFrame(avg_prices_data)
            
            fig_avg = px.bar(
                avg_prices_df.melt(id_vars=['Proveedor'], 
                                   value_vars=['Promedio 20\'', 'Promedio 40\''],
                                   var_name='Tipo Contenedor', value_name='Precio Promedio'),
                x='Proveedor',
                y='Precio Promedio',
                color='Tipo Contenedor',
                title="Comparación de Precios Promedio por Proveedor",
                barmode='group'
            )
            
            st.plotly_chart(fig_avg, use_container_width=True)
        
        # Análisis de competitividad
        st.subheader("Análisis de Competitividad")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Rendimiento por Proveedor (Contenedor 20')**")
            performance_20 = comparison_df['best_provider_20'].value_counts()
            performance_20_df = pd.DataFrame({
                'Proveedor': performance_20.index,
                'Mejores Precios': performance_20.values,
                'Porcentaje': (performance_20.values / performance_20.sum() * 100).round(1)
            })
            st.dataframe(performance_20_df, use_container_width=True)
        
        with col2:
            st.write("**Rendimiento por Proveedor (Contenedor 40')**")
            performance_40 = comparison_df['best_provider_40'].value_counts()
            performance_40_df = pd.DataFrame({
                'Proveedor': performance_40.index,
                'Mejores Precios': performance_40.values,
                'Porcentaje': (performance_40.values / performance_40.sum() * 100).round(1)
            })
            st.dataframe(performance_40_df, use_container_width=True)

with tab4:
    st.header("🗺️ Destinos sin Coincidencias")
    
    if not no_matches_df.empty:
        st.write(f"Total de destinos disponibles en una sola fuente: **{len(no_matches_df)}**")
        
        # Distribución por fuente
        source_dist = no_matches_df['source'].value_counts()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Distribución por Fuente")
            source_dist_df = pd.DataFrame({
                'Fuente': source_dist.index,
                'Cantidad': source_dist.values,
                'Porcentaje': (source_dist.values / source_dist.sum() * 100).round(1)
            })
            st.dataframe(source_dist_df, use_container_width=True)
        
        with col2:
            fig_source = px.pie(
                values=source_dist.values,
                names=source_dist.index,
                title="Destinos Únicos por Fuente"
            )
            st.plotly_chart(fig_source, use_container_width=True)
        
        # Tabla detallada de destinos sin coincidencias
        st.subheader("Detalle de Destinos sin Coincidencias")
        
        # Filtro por fuente
        fuentes_disponibles = no_matches_df['source'].unique().tolist()
        fuente_selected = st.selectbox(
            "Filtrar por fuente:",
            options=["Todas"] + fuentes_disponibles
        )
        
        if fuente_selected != "Todas":
            no_matches_filtered = no_matches_df[no_matches_df['source'] == fuente_selected]
        else:
            no_matches_filtered = no_matches_df
        
        # Mostrar tabla
        display_df = no_matches_filtered[['destino', 'source', 'veinte', 'cuarenta']].copy()
        display_df.columns = ['Destino', 'Fuente', 'Precio 20\'', 'Precio 40\'']
        display_df = display_df.fillna('N/A')
        
        st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info("No hay destinos sin coincidencias en los datos.")

with tab5:
    st.header("📋 Datos Detallados")
    
    # Selector de dataset
    dataset_option = st.selectbox(
        "Seleccionar dataset:",
        options=[
            "Comparación de Precios",
            "Datos AiresDS",
            "Datos FCL", 
            "Datos Silver",
            "Estadísticas Resumen"
        ]
    )
    
    if dataset_option == "Comparación de Precios":
        st.subheader("Datos de Comparación de Precios")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Opción de descarga
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Descargar datos filtrados como CSV",
            data=csv,
            file_name="comparacion_precios_filtrada.csv",
            mime="text/csv"
        )
    
    elif dataset_option == "Datos AiresDS":
        st.subheader("Datos de AiresDS")
        st.dataframe(airesds_df, use_container_width=True)
    
    elif dataset_option == "Datos FCL":
        st.subheader("Datos de FCL")
        st.dataframe(fcl_df, use_container_width=True)
    
    elif dataset_option == "Datos Silver":
        st.subheader("Datos de Silver")
        st.dataframe(silver_df, use_container_width=True)
    
    elif dataset_option == "Estadísticas Resumen":
        st.subheader("Estadísticas de Resumen")
        summary_display = summary_stats.copy()
        summary_display.index = [
            "Total destinos comparados",
            "Diferencia promedio 20' (%)",
            "Diferencia máxima 20' (%)", 
            "Diferencia promedio 40' (%)",
            "Diferencia máxima 40' (%)",
            "AiresDS mejores precios 20'",
            "FCL mejores precios 20'",
            "Silver mejores precios 20'",
            "AiresDS mejores precios 40'",
            "FCL mejores precios 40'",
            "Silver mejores precios 40'"
        ]
        st.dataframe(summary_display, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Dashboard de Comparación de Precios Marítimos** | Generado automáticamente desde los datos de comparacion.py")
    



