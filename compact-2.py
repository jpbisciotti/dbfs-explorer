=============================================================================
# DATABRICKS FILE EXPLORER - HTML/JavaScript Version
# =============================================================================
# Copy this entire cell into a Databricks notebook and run it.
# This version uses displayHTML() which renders properly in Databricks.
# =============================================================================

import os
import json
from datetime import datetime

def get_directory_contents(path):
    """Get directory contents with metadata"""
    items = []
    try:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            try:
                stat_info = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                
                # Get file extension and icon
                ext = os.path.splitext(name)[1].lower()
                icons = {
                    '.py': '🐍', '.ipynb': '📓', '.sql': '🗃️', '.csv': '📊',
                    '.json': '📋', '.parquet': '📦', '.txt': '📄', '.md': '📝',
                    '.sh': '💻', '.jar': '☕', '.scala': '🔷', '.html': '🌐',
                    '.pdf': '📕', '.zip': '🗜️', '.png': '🖼️', '.jpg': '🖼️',
                    '.xml': '📰', '.yaml': '⚙️', '.yml': '⚙️', '.log': '📜',
                    '.delta': '🔺', '.r': '📈'
                }
                icon = '📁' if is_dir else icons.get(ext, '📄')
                
                # Get file type
                types = {
                    '.py': 'Python', '.ipynb': 'Notebook', '.sql': 'SQL',
                    '.csv': 'CSV', '.json': 'JSON', '.parquet': 'Parquet',
                    '.txt': 'Text', '.md': 'Markdown', '.html': 'HTML',
                    '.pdf': 'PDF', '.zip': 'Archive'
                }
                file_type = 'Folder' if is_dir else types.get(ext, ext[1:].upper() if ext else 'File')
                
                # Format size
                size = stat_info.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024**2:
                    size_str = f"{size/1024:.1f} KB"
                elif size < 1024**3:
                    size_str = f"{size/1024**2:.1f} MB"
                else:
                    size_str = f"{size/1024**3:.1f} GB"
                
                items.append({
                    'name': name,
                    'path': full_path,
                    'is_dir': is_dir,
                    'size': size,
                    'size_str': size_str if not is_dir else '--',
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'modified_ts': stat_info.st_mtime,
                    'icon': icon,
                    'type': file_type
                })
            except (PermissionError, OSError) as e:
                items.append({
                    'name': name,
                    'path': full_path,
                    'is_dir': False,
                    'size': 0,
                    'size_str': '??',
                    'modified': 'Unknown',
                    'modified_ts': 0,
                    'icon': '⚠️',
                    'type': 'Unknown'
                })
    except PermissionError:
        pass
    except Exception as e:
        pass
    
    # Sort: directories first, then by name
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    return items

def create_file_explorer(start_path=None):
    """Create and display the file explorer"""
    
    if start_path is None:
        start_path = os.getcwd()
    
    start_path = os.path.abspath(start_path)
    items = get_directory_contents(start_path)
    items_json = json.dumps(items)
    
    html = f'''
    <div id="file-explorer-app">
        <style>
            #file-explorer-app {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                max-width: 900px;
                border: 2px solid #1a73e8;
                border-radius: 10px;
                padding: 15px;
                background: #fff;
            }}
            #fe-header {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
            }}
            #fe-header h2 {{
                margin: 0;
                color: #1a73e8;
                flex-grow: 1;
            }}
            .fe-btn {{
                padding: 8px 12px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            }}
            .fe-btn:hover {{ opacity: 0.8; }}
            .fe-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .fe-btn-nav {{ background: #1a73e8; color: white; }}
            .fe-btn-up {{ background: #f59e0b; color: white; }}
            .fe-btn-home {{ background: #10b981; color: white; }}
            .fe-btn-refresh {{ background: #6b7280; color: white; }}
            
            #fe-path-bar {{
                display: flex;
                gap: 5px;
                margin: 10px 0;
                align-items: center;
            }}
            #fe-path-input {{
                flex-grow: 1;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }}
            #fe-go-btn {{
                background: #1a73e8;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            
            #fe-toolbar {{
                display: flex;
                gap: 15px;
                margin: 10px 0;
                align-items: center;
                flex-wrap: wrap;
            }}
            #fe-search {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                width: 200px;
            }}
            #fe-sort {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            
            #fe-list-header {{
                display: grid;
                grid-template-columns: 50px 1fr 100px 140px 100px;
                background: #e5e7eb;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px 5px 0 0;
                font-size: 14px;
            }}
            #fe-file-list {{
                border: 1px solid #ddd;
                border-top: none;
                max-height: 400px;
                overflow-y: auto;
                border-radius: 0 0 5px 5px;
            }}
            .fe-item {{
                display: grid;
                grid-template-columns: 50px 1fr 100px 140px 100px;
                padding: 10px;
                border-bottom: 1px solid #eee;
                cursor: pointer;
                transition: background 0.2s;
                align-items: center;
            }}
            .fe-item:hover {{ background: #e3f2fd; }}
            .fe-item-dir {{ font-weight: 500; }}
            .fe-item-icon {{ font-size: 1.3em; }}
            .fe-item-name {{ 
                overflow: hidden; 
                text-overflow: ellipsis; 
                white-space: nowrap;
            }}
            .fe-item-meta {{ color: #666; font-size: 0.9em; }}
            
            #fe-status {{
                margin: 10px 0;
                color: #666;
                font-size: 14px;
            }}
            
            #fe-details {{
                background: #f5f5f5;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                border-left: 4px solid #1a73e8;
            }}
            #fe-details h4 {{ margin: 0 0 10px 0; }}
            #fe-details table {{ width: 100%; font-size: 14px; }}
            #fe-details td {{ padding: 4px 8px; }}
            #fe-details td:first-child {{ font-weight: bold; width: 120px; }}
            
            .fe-empty {{
                padding: 40px;
                text-align: center;
                color: #666;
                font-style: italic;
            }}
            
            #fe-breadcrumb {{
                padding: 8px;
                background: #f0f7ff;
                border-radius: 5px;
                margin: 5px 0;
                font-size: 14px;
            }}
            .fe-crumb {{
                color: #1a73e8;
                cursor: pointer;
                text-decoration: none;
            }}
            .fe-crumb:hover {{ text-decoration: underline; }}
        </style>
        
        <div id="fe-header">
            <h2>📁 Databricks File Explorer</h2>
        </div>
        
        <div id="fe-nav-buttons">
            <button class="fe-btn fe-btn-nav" id="fe-back-btn" onclick="goBack()" disabled>◀ Back</button>
            <button class="fe-btn fe-btn-nav" id="fe-fwd-btn" onclick="goForward()" disabled>Forward ▶</button>
            <button class="fe-btn fe-btn-up" onclick="goUp()">⬆ Up</button>
            <button class="fe-btn fe-btn-home" onclick="goHome()">🏠 Home</button>
            <button class="fe-btn fe-btn-refresh" onclick="refresh()">🔄 Refresh</button>
        </div>
        
        <div id="fe-path-bar">
            <strong>Path:</strong>
            <input type="text" id="fe-path-input" value="{start_path}" onkeypress="if(event.key==='Enter')navigateTo(this.value)">
            <button id="fe-go-btn" onclick="navigateTo(document.getElementById('fe-path-input').value)">Go</button>
        </div>
        
        <div id="fe-breadcrumb"></div>
        
        <div id="fe-toolbar">
            <input type="text" id="fe-search" placeholder="🔍 Search files..." oninput="filterItems()">
            <label>Sort by: 
                <select id="fe-sort" onchange="sortItems()">
                    <option value="name">Name</option>
                    <option value="size">Size</option>
                    <option value="date">Date</option>
                    <option value="type">Type</option>
                </select>
            </label>
            <label>
                <input type="checkbox" id="fe-sort-desc" onchange="sortItems()"> Descending
            </label>
        </div>
        
        <div id="fe-list-header">
            <span></span>
            <span>Name</span>
            <span>Size</span>
            <span>Modified</span>
            <span>Type</span>
        </div>
        
        <div id="fe-file-list"></div>
        
        <div id="fe-status">Loading...</div>
        
        <div id="fe-details">
            <em>Click on a file to view details</em>
        </div>
        
        <script>
            (function() {{
                // State
                let currentPath = "{start_path}";
                let allItems = {items_json};
                let history = [currentPath];
                let historyIndex = 0;
                
                // Initialize
                window.feCurrentPath = currentPath;
                window.feAllItems = allItems;
                
                renderItems(allItems);
                updateBreadcrumb();
                updateStatus();
                
                // Make functions global for onclick handlers
                window.goBack = function() {{
                    if (historyIndex > 0) {{
                        historyIndex--;
                        navigateTo(history[historyIndex], false);
                    }}
                }};
                
                window.goForward = function() {{
                    if (historyIndex < history.length - 1) {{
                        historyIndex++;
                        navigateTo(history[historyIndex], false);
                    }}
                }};
                
                window.goUp = function() {{
                    const parent = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
                    navigateTo(parent);
                }};
                
                window.goHome = function() {{
                    navigateTo('/home');
                }};
                
                window.refresh = function() {{
                    // In static HTML we can't refresh, show message
                    document.getElementById('fe-status').innerHTML = '🔄 To refresh, re-run the cell with: create_file_explorer("' + currentPath + '")';
                }};
                
                window.navigateTo = function(path, addToHistory = true) {{
                    // In static HTML, we need to re-run Python
                    // Show instructions to user
                    const status = document.getElementById('fe-status');
                    status.innerHTML = '📂 To navigate to <strong>' + path + '</strong>, run: <code>create_file_explorer("' + path + '")</code>';
                    document.getElementById('fe-path-input').value = path;
                }};
                
                window.filterItems = function() {{
                    const query = document.getElementById('fe-search').value.toLowerCase();
                    const filtered = allItems.filter(item => 
                        item.name.toLowerCase().includes(query)
                    );
                    renderItems(filtered);
                    updateStatus(filtered);
                }};
                
                window.sortItems = function() {{
                    const sortBy = document.getElementById('fe-sort').value;
                    const desc = document.getElementById('fe-sort-desc').checked;
                    
                    const sorted = [...allItems].sort((a, b) => {{
                        // Directories always first
                        if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
                        
                        let cmp = 0;
                        switch(sortBy) {{
                            case 'name': cmp = a.name.toLowerCase().localeCompare(b.name.toLowerCase()); break;
                            case 'size': cmp = a.size - b.size; break;
                            case 'date': cmp = a.modified_ts - b.modified_ts; break;
                            case 'type': cmp = a.type.localeCompare(b.type); break;
                        }}
                        return desc ? -cmp : cmp;
                    }});
                    
                    renderItems(sorted);
                }};
                
                window.showDetails = function(index) {{
                    const item = allItems[index];
                    const details = document.getElementById('fe-details');
                    details.innerHTML = `
                        <h4>${{item.icon}} ${{item.name}}</h4>
                        <table>
                            <tr><td>Full Path:</td><td style="word-break:break-all">${{item.path}}</td></tr>
                            <tr><td>Type:</td><td>${{item.type}}</td></tr>
                            <tr><td>Size:</td><td>${{item.size_str}} ${{item.is_dir ? '' : '(' + item.size.toLocaleString() + ' bytes)'}}</td></tr>
                            <tr><td>Modified:</td><td>${{item.modified}}</td></tr>
                        </table>
                        ${{item.is_dir ? '<p style="margin-top:10px"><em>Run <code>create_file_explorer("' + item.path + '")</code> to open this folder</em></p>' : ''}}
                    `;
                }};
                
                function renderItems(items) {{
                    const container = document.getElementById('fe-file-list');
                    
                    if (items.length === 0) {{
                        container.innerHTML = '<div class="fe-empty">No items to display</div>';
                        return;
                    }}
                    
                    container.innerHTML = items.map((item, i) => `
                        <div class="fe-item ${{item.is_dir ? 'fe-item-dir' : ''}}" 
                             onclick="showDetails(${{allItems.indexOf(item)}})${{item.is_dir ? '; navigateTo(\\'' + item.path.replace(/'/g, "\\\\'") + '\\')' : ''}}">
                            <span class="fe-item-icon">${{item.icon}}</span>
                            <span class="fe-item-name" title="${{item.name}}">${{item.name}}</span>
                            <span class="fe-item-meta">${{item.size_str}}</span>
                            <span class="fe-item-meta">${{item.modified}}</span>
                            <span class="fe-item-meta">${{item.type}}</span>
                        </div>
                    `).join('');
                }}
                
                function updateBreadcrumb() {{
                    const parts = currentPath.split('/').filter(p => p);
                    let path = '';
                    const crumbs = ['<span class="fe-crumb" onclick="navigateTo(\\'/'\\')">🏠 /</span>'];
                    
                    parts.forEach((part, i) => {{
                        path += '/' + part;
                        const isLast = i === parts.length - 1;
                        if (isLast) {{
                            crumbs.push('<strong>' + part + '</strong>');
                        }} else {{
                            crumbs.push('<span class="fe-crumb" onclick="navigateTo(\\'' + path + '\\')">' + part + '</span>');
                        }}
                    }});
                    
                    document.getElementById('fe-breadcrumb').innerHTML = crumbs.join(' / ');
                }}
                
                function updateStatus(items = allItems) {{
                    const dirs = items.filter(i => i.is_dir).length;
                    const files = items.length - dirs;
                    const totalSize = items.filter(i => !i.is_dir).reduce((sum, i) => sum + i.size, 0);
                    
                    let sizeStr = '';
                    if (totalSize > 0) {{
                        if (totalSize < 1024) sizeStr = totalSize + ' B';
                        else if (totalSize < 1024**2) sizeStr = (totalSize/1024).toFixed(1) + ' KB';
                        else if (totalSize < 1024**3) sizeStr = (totalSize/1024**2).toFixed(1) + ' MB';
                        else sizeStr = (totalSize/1024**3).toFixed(1) + ' GB';
                    }}
                    
                    document.getElementById('fe-status').innerHTML = 
                        `${{dirs}} folder(s), ${{files}} file(s)${{sizeStr ? ' | Total: ' + sizeStr : ''}}`;
                }}
            }})();
        </script>
    </div>
    '''
    
    displayHTML(html)

# =============================================================================
# LAUNCH THE EXPLORER
# =============================================================================
# Change the path as needed:
# - "/" for root
# - "/dbfs" for DBFS  
# - "/Workspace" for workspace
# - os.getcwd() for current directory

create_file_explorer(os.getcwd())

# To navigate to a different folder, run:
# create_file_explorer("/your/path/here")
