import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

def extract_port_code(destination):
    """
    Extract port code from destination string.
    Port codes are typically 4 uppercase letters in parentheses.
    """
    if pd.isna(destination):
        return ""
    
    dest = str(destination).strip()
    
    # Look for pattern like (ABCD) where ABCD is 4 uppercase letters
    port_match = re.search(r'\(([A-Z]{4})\)', dest)
    if port_match:
        return port_match.group(1)
    
    # Alternative pattern: look for 4 consecutive uppercase letters
    alt_match = re.search(r'\b([A-Z]{4})\b', dest)
    if alt_match:
        return alt_match.group(1)
    
    return ""

def extract_city_name(destination):
    """
    Extract the main city name from destination string.
    Removes everything after '(' or '-' and cleans the string.
    """
    if pd.isna(destination):
        return ""
    
    # Convert to string and strip whitespace
    dest = str(destination).strip()
    
    # Remove everything after '(' or '-'
    # Split by '(' first, then by '-'
    if '(' in dest:
        dest = dest.split('(')[0].strip()
    if '-' in dest:
        dest = dest.split('-')[0].strip()
    if '/' in dest:
        dest = dest.split('/')[0].strip()
    
    # Clean and normalize
    dest = re.sub(r'\s+', ' ', dest)  # Replace multiple spaces with single space
    dest = dest.lower().strip()
    
    return dest

def similarity_score(str1, str2):
    """Calculate similarity score between two strings."""
    return SequenceMatcher(None, str1, str2).ratio()

def find_best_match(destination, destination_list, threshold=0.8):
    """
    Find the best matching destination from a list.
    Returns the best match if similarity is above threshold, otherwise None.
    """
    city_name = extract_city_name(destination)
    if not city_name:
        return None
    
    best_match = None
    best_score = 0
    
    for dest in destination_list:
        dest_city = extract_city_name(dest)
        if dest_city:
            score = similarity_score(city_name, dest_city)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = dest
    
    return best_match

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

# Add port code extraction to all datasets
airesds['port_code'] = airesds['destino'].apply(extract_port_code)
fcl['port_code'] = fcl['destino'].apply(extract_port_code)
silver['port_code'] = silver['destino'].apply(extract_port_code)

# Add source columns
airesds['source'] = 'AiresDS'
fcl['source'] = 'FCL'
silver['source'] = 'Silver'

# Create a comprehensive comparison with improved matching
all_destinations = set(airesds['destino'].tolist() + fcl['destino'].tolist() + silver['destino'].tolist())

# Create mapping dictionaries for fuzzy matching
airesds_destinations = airesds['destino'].tolist()
fcl_destinations = fcl['destino'].tolist()
silver_destinations = silver['destino'].tolist()

comparison_data = []
no_matches_data = []
matched_destinations = set()

print("Starting destination matching process...")
print(f"Total unique destinations found: {len(all_destinations)}")

for destino in all_destinations:
    if destino in matched_destinations:
        continue  # Skip if already processed as part of a match
    
    # Extract port code for current destination
    current_port_code = extract_port_code(destino)
    
    # Try exact match first
    aires_data = airesds[airesds['destino'] == destino]
    fcl_data = fcl[fcl['destino'] == destino]
    silver_data = silver[silver['destino'] == destino]
    
    # If no exact matches, try fuzzy matching (city name only, not port code)
    aires_match = destino if len(aires_data) > 0 else find_best_match(destino, airesds_destinations)
    fcl_match = destino if len(fcl_data) > 0 else find_best_match(destino, fcl_destinations)
    silver_match = destino if len(silver_data) > 0 else find_best_match(destino, silver_destinations)
    
    # Get data based on matches (exact or fuzzy)
    if aires_match:
        aires_data = airesds[airesds['destino'] == aires_match]
        matched_destinations.add(aires_match)
    if fcl_match:
        fcl_data = fcl[fcl['destino'] == fcl_match]
        matched_destinations.add(fcl_match)
    if silver_match:
        silver_data = silver[silver['destino'] == silver_match]
        matched_destinations.add(silver_match)
    
    # Add current destination to matched set
    matched_destinations.add(destino)
    
    # Check if destination exists in each dataset
    has_aires = len(aires_data) > 0
    has_fcl = len(fcl_data) > 0
    has_silver = len(silver_data) > 0
    
    # Count available sources
    sources_count = sum([has_aires, has_fcl, has_silver])
    
    if sources_count >= 2:  # At least 2 sources for comparison
        # Determine the primary destination name (prefer exact matches)
        primary_destino = destino
        if aires_match and aires_match != destino:
            primary_destino = f"{destino} / {aires_match}"
        elif fcl_match and fcl_match != destino:
            primary_destino = f"{destino} / {fcl_match}"
        elif silver_match and silver_match != destino:
            primary_destino = f"{destino} / {silver_match}"
        
        row = {'destino': primary_destino}
        
        # Add port code information for visualization
        row['port_code'] = current_port_code
        if not current_port_code and aires_match:
            row['port_code'] = extract_port_code(aires_match)
        if not row['port_code'] and fcl_match:
            row['port_code'] = extract_port_code(fcl_match)
        if not row['port_code'] and silver_match:
            row['port_code'] = extract_port_code(silver_match)
        
        # Store original destination names for reference
        row['aires_original'] = aires_match if has_aires else None
        row['fcl_original'] = fcl_match if has_fcl else None
        row['silver_original'] = silver_match if has_silver else None
        
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
        row['match_type'] = 'exact' if (aires_match == destino and fcl_match == destino and silver_match == destino) else 'fuzzy'
        comparison_data.append(row)
        
        # Print matching info for fuzzy matches
        if row['match_type'] == 'fuzzy':
            matches_info = []
            if has_aires and aires_match != destino:
                matches_info.append(f"AiresDS: {aires_match}")
            if has_fcl and fcl_match != destino:
                matches_info.append(f"FCL: {fcl_match}")
            if has_silver and silver_match != destino:
                matches_info.append(f"Silver: {silver_match}")
            
            if matches_info:
                print(f"Fuzzy match found for '{destino}' -> {', '.join(matches_info)}")
    
    else:  # Destinations with no matches (only in one source)
        source_name = 'AiresDS' if has_aires else ('FCL' if has_fcl else 'Silver')
        data = aires_data if has_aires else (fcl_data if has_fcl else silver_data)
        original_dest = aires_match if has_aires else (fcl_match if has_fcl else silver_match)
        
        no_match_row = {
            'destino': destino,
            'original_destino': original_dest,
            'port_code': current_port_code,
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

print("Price Comparison Report Generated with Improved Matching!")
print(f"Total destinations compared: {len(comparison_df)}")
print(f"Destinations with no matches: {len(no_matches_df)}")
print(f"Report saved as 'price_comparison_report.xlsx'")
print("CSV files saved in 'data' folder")

# Count fuzzy matches
if not comparison_df.empty and 'match_type' in comparison_df.columns:
    fuzzy_matches = len(comparison_df[comparison_df['match_type'] == 'fuzzy'])
    exact_matches = len(comparison_df[comparison_df['match_type'] == 'exact'])
    print(f"Exact matches: {exact_matches}")
    print(f"Fuzzy matches (improved matching): {fuzzy_matches}")

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