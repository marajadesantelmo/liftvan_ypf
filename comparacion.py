import pandas as pd
import numpy as np

# Read and clean data
airesds = pd.read_excel('airesds.xlsx')
fcl = pd.read_excel('fcl.xlsx')
silver = pd.read_excel('silver.xlsx')

# Clean AiresDS data
airesds = airesds.dropna(subset=['veinte', 'curenta'])
airesds = airesds[~airesds['destino'].str.startswith('*')]
airesds = airesds[~airesds['destino'].str.contains('HAPAG:', na=False)]
airesds['veinte'] = airesds['veinte'].replace({'\$': '', ',': ''}, regex=True).astype(float)
airesds['curenta'] = airesds['curenta'].replace({'\$': '', ',': ''}, regex=True).astype(float)
airesds = airesds.reset_index(drop=True)

# Rename columns for consistency
airesds.rename(columns={'curenta': 'cuarenta'}, inplace=True)

# Clean FCL data (remove $ and commas if present)
if fcl['veinte'].dtype == 'object':
    fcl['veinte'] = fcl['veinte'].replace({'\$': '', ',': ''}, regex=True).astype(float)
if fcl['cuarenta'].dtype == 'object':
    fcl['cuarenta'] = fcl['cuarenta'].replace({'\$': '', ',': ''}, regex=True).astype(float)

# Clean Silver data (remove $ and commas if present)
if silver['veinte'].dtype == 'object':
    silver['veinte'] = silver['veinte'].replace({'\$': '', ',': ''}, regex=True).astype(float)
if silver['cuarenta'].dtype == 'object':
    silver['cuarenta'] = silver['cuarenta'].replace({'\$': '', ',': ''}, regex=True).astype(float)

# Add source columns
airesds['source'] = 'AiresDS'
fcl['source'] = 'FCL'
silver['source'] = 'Silver'

# Create a comprehensive comparison
all_destinations = set(airesds['destino'].tolist() + fcl['destino'].tolist() + silver['destino'].tolist())

comparison_data = []
no_matches_data = []

for destino in all_destinations:
    # Get prices from each source
    aires_data = airesds[airesds['destino'] == destino]
    fcl_data = fcl[fcl['destino'] == destino]
    silver_data = silver[silver['destino'] == destino]
    
    # Check if destination exists in each dataset
    has_aires = len(aires_data) > 0
    has_fcl = len(fcl_data) > 0
    has_silver = len(silver_data) > 0
    
    # Count available sources
    sources_count = sum([has_aires, has_fcl, has_silver])
    
    if sources_count >= 2:  # At least 2 sources for comparison
        row = {'destino': destino}
        
        # AiresDS prices
        if has_aires:
            row['aires_20'] = aires_data.iloc[0]['veinte']
            row['aires_40'] = aires_data.iloc[0]['cuarenta']
        else:
            row['aires_20'] = np.nan
            row['aires_40'] = np.nan
        
        # FCL prices
        if has_fcl:
            row['fcl_20'] = fcl_data.iloc[0]['veinte']
            row['fcl_40'] = fcl_data.iloc[0]['cuarenta']
        else:
            row['fcl_20'] = np.nan
            row['fcl_40'] = np.nan
        
        # Silver prices
        if has_silver:
            row['silver_20'] = silver_data.iloc[0]['veinte']
            row['silver_40'] = silver_data.iloc[0]['cuarenta']
        else:
            row['silver_20'] = np.nan
            row['silver_40'] = np.nan
        
        # Calculate differences and best prices for 20'
        prices_20 = [p for p in [row.get('aires_20'), row.get('fcl_20'), row.get('silver_20')] if pd.notna(p)]
        if prices_20:
            row['best_price_20'] = min(prices_20)
            row['worst_price_20'] = max(prices_20)
            row['price_diff_20'] = max(prices_20) - min(prices_20)
            row['price_diff_20_pct'] = (row['price_diff_20'] / min(prices_20)) * 100
            
            # Find best provider for 20'
            if pd.notna(row.get('aires_20')) and row['aires_20'] == row['best_price_20']:
                row['best_provider_20'] = 'AiresDS'
            elif pd.notna(row.get('fcl_20')) and row['fcl_20'] == row['best_price_20']:
                row['best_provider_20'] = 'FCL'
            else:
                row['best_provider_20'] = 'Silver'
        
        # Calculate differences and best prices for 40'
        prices_40 = [p for p in [row.get('aires_40'), row.get('fcl_40'), row.get('silver_40')] if pd.notna(p)]
        if prices_40:
            row['best_price_40'] = min(prices_40)
            row['worst_price_40'] = max(prices_40)
            row['price_diff_40'] = max(prices_40) - min(prices_40)
            row['price_diff_40_pct'] = (row['price_diff_40'] / min(prices_40)) * 100
            
            # Find best provider for 40'
            if pd.notna(row.get('aires_40')) and row['aires_40'] == row['best_price_40']:
                row['best_provider_40'] = 'AiresDS'
            elif pd.notna(row.get('fcl_40')) and row['fcl_40'] == row['best_price_40']:
                row['best_provider_40'] = 'FCL'
            else:
                row['best_provider_40'] = 'Silver'
        
        row['sources_available'] = sources_count
        comparison_data.append(row)
    
    else:  # Destinations with no matches (only in one source)
        source_name = 'AiresDS' if has_aires else ('FCL' if has_fcl else 'Silver')
        data = aires_data if has_aires else (fcl_data if has_fcl else silver_data)
        
        no_match_row = {
            'destino': destino,
            'source': source_name,
            'veinte': data.iloc[0]['veinte'] if len(data) > 0 else np.nan,
            'cuarenta': data.iloc[0]['cuarenta'] if len(data) > 0 else np.nan,
            'reason': 'Only available in one source'
        }
        no_matches_data.append(no_match_row)

# Create DataFrames
comparison_df = pd.DataFrame(comparison_data)
no_matches_df = pd.DataFrame(no_matches_data)

# Sort by price difference for better analysis
if not comparison_df.empty:
    comparison_df = comparison_df.sort_values('price_diff_20_pct', ascending=False, na_position='last')

# Create summary statistics
summary_stats = {}
if not comparison_df.empty:
    summary_stats = {
        'total_destinations_compared': len(comparison_df),
        'avg_price_diff_20_pct': comparison_df['price_diff_20_pct'].mean(),
        'max_price_diff_20_pct': comparison_df['price_diff_20_pct'].max(),
        'avg_price_diff_40_pct': comparison_df['price_diff_40_pct'].mean(),
        'max_price_diff_40_pct': comparison_df['price_diff_40_pct'].max(),
        'aires_best_count_20': (comparison_df['best_provider_20'] == 'AiresDS').sum(),
        'fcl_best_count_20': (comparison_df['best_provider_20'] == 'FCL').sum(),
        'silver_best_count_20': (comparison_df['best_provider_20'] == 'Silver').sum(),
        'aires_best_count_40': (comparison_df['best_provider_40'] == 'AiresDS').sum(),
        'fcl_best_count_40': (comparison_df['best_provider_40'] == 'FCL').sum(),
        'silver_best_count_40': (comparison_df['best_provider_40'] == 'Silver').sum(),
    }

# Save to Excel with multiple sheets
with pd.ExcelWriter('price_comparison_report.xlsx', engine='openpyxl') as writer:
    # Main comparison sheet
    comparison_df.to_excel(writer, sheet_name='Price Comparison', index=False)
    
    # No matches sheet
    no_matches_df.to_excel(writer, sheet_name='No Matches', index=False)
    
    # Summary statistics
    summary_df = pd.DataFrame([summary_stats]).T
    summary_df.columns = ['Value']
    summary_df.to_excel(writer, sheet_name='Summary Statistics')
    
    # Individual source data for reference
    airesds.to_excel(writer, sheet_name='AiresDS Data', index=False)
    fcl.to_excel(writer, sheet_name='FCL Data', index=False)
    silver.to_excel(writer, sheet_name='Silver Data', index=False)

# Save each sheet as CSV in data folder
comparison_df.to_csv('data/price_comparison.csv', index=False)
no_matches_df.to_csv('data/no_matches.csv', index=False)
summary_df = pd.DataFrame([summary_stats]).T
summary_df.columns = ['Value']
summary_df.to_csv('data/summary_statistics.csv')
airesds.to_csv('data/airesds_data.csv', index=False)
fcl.to_csv('data/fcl_data.csv', index=False)
silver.to_csv('data/silver_data.csv', index=False)

print("Price Comparison Report Generated!")
print(f"Total destinations compared: {len(comparison_df)}")
print(f"Destinations with no matches: {len(no_matches_df)}")
print(f"Report saved as 'price_comparison_report.xlsx'")
print("CSV files saved in 'data' folder")

# Display top 10 biggest price differences
print("\nTop 10 destinations with biggest price differences (20' containers):")
if not comparison_df.empty:
    top_diffs = comparison_df.nlargest(10, 'price_diff_20_pct')[['destino', 'price_diff_20_pct', 'best_provider_20']]
    print(top_diffs.to_string(index=False))

# Display provider performance summary
print(f"\nProvider Performance Summary (20' containers):")
if 'aires_best_count_20' in summary_stats:
    print(f"AiresDS best prices: {summary_stats['aires_best_count_20']}")
    print(f"FCL best prices: {summary_stats['fcl_best_count_20']}")
    print(f"Silver best prices: {summary_stats['silver_best_count_20']}")