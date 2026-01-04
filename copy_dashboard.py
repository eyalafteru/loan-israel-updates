import shutil
import os

# Copy dashboard.html to v2
src = 'dashboard.html'
dst = 'v2/dashboard/dashboard_full.html'

shutil.copy(src, dst)
print(f'Copied {src} to {dst}')

# Also copy the js folder content if needed
if os.path.exists('js/keywordDensityAnalyzer.js'):
    shutil.copy('js/keywordDensityAnalyzer.js', 'v2/dashboard/analyzers_full.js')
    print('Copied js/keywordDensityAnalyzer.js to v2/dashboard/analyzers_full.js')

print('Done!')

