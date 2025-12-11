# Databricks File Explorer
# Copy and paste this code into a Databricks notebook cell and run it

# Install ipywidgets if needed (uncomment if necessary)
# %pip install ipywidgets

import os
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
from datetime import datetime
from pathlib import Path
import fnmatch

class DatabricksFileExplorer:
    """
    Interactive File Explorer for Databricks Notebooks
    
    Features:
    - Navigate directories with mouse clicks
    - View file metadata (size, modified date, type)
    - Back/Forward navigation with history
    - Breadcrumb navigation
    - Search functionality
    - Sort by name, size, or date
    """
    
    def __init__(self, start_path="/"):
        # Navigation history
        self.history = []
        self.history_index = -1
        self.current_path = start_path
        
        # Sorting state
        self.sort_by = "name"
        self.sort_reverse = False
        
        # Search state
        self.search_query = ""
        
        # Build UI components
        self._build_ui()
        
        # Initial navigation
        self._navigate_to(start_path, add_to_history=True)
    
    def _build_ui(self):
        """Build the user interface components"""
        
        # === HEADER SECTION ===
        # Title
        self.title = widgets.HTML(
            value="<h2 style='margin: 0; color: #1a73e8;'>ð Databricks File Explorer</h2>"
        )
        
        # Navigation buttons
        self.back_btn = widgets.Button(
            description="â Back",
            disabled=True,
            button_style='info',
            layout=widgets.Layout(width='80px')
        )
        self.back_btn.on_click(self._go_back)
        
        self.forward_btn = widgets.Button(
            description="Forward â¶",
            disabled=True,
            button_style='info',
            layout=widgets.Layout(width='90px')
        )
        self.forward_btn.on_click(self._go_forward)
        
        self.up_btn = widgets.Button(
            description="â¬ Up",
            button_style='warning',
            layout=widgets.Layout(width='70px')
        )
        self.up_btn.on_click(self._go_up)
        
        self.home_btn = widgets.Button(
            description="ð  Home",
            button_style='success',
            layout=widgets.Layout(width='80px')
        )
        self.home_btn.on_click(self._go_home)
        
        self.refresh_btn = widgets.Button(
            description="ð Refresh",
            button_style='',
            layout=widgets.Layout(width='90px')
        )
        self.refresh_btn.on_click(self._refresh)
        
        # Navigation button row
        self.nav_buttons = widgets.HBox([
            self.back_btn, 
            self.forward_btn, 
            self.up_btn, 
            self.home_btn, 
            self.refresh_btn
        ], layout=widgets.Layout(margin='5px 0'))
        
        # === PATH BAR ===
        self.path_input = widgets.Text(
            value=self.current_path,
            placeholder='Enter path...',
            layout=widgets.Layout(width='70%')
        )
        self.path_input.on_submit(self._on_path_submit)
        
        self.go_btn = widgets.Button(
            description="Go",
            button_style='primary',
            layout=widgets.Layout(width='60px')
        )
        self.go_btn.on_click(self._on_go_click)
        
        self.path_bar = widgets.HBox([
            widgets.HTML("<b>Path:</b>&nbsp;"),
            self.path_input, 
            self.go_btn
        ], layout=widgets.Layout(margin='5px 0'))
        
        # === BREADCRUMB NAVIGATION ===
        self.breadcrumb = widgets.HTML(value="")
        
        # === SEARCH BAR ===
        self.search_input = widgets.Text(
            placeholder='ð Search files and folders...',
            layout=widgets.Layout(width='300px')
        )
        self.search_input.observe(self._on_search_change, names='value')
        
        self.clear_search_btn = widgets.Button(
            description="Clear",
            layout=widgets.Layout(width='60px')
        )
        self.clear_search_btn.on_click(self._clear_search)
        
        self.search_bar = widgets.HBox([
            self.search_input,
            self.clear_search_btn
        ], layout=widgets.Layout(margin='5px 0'))
        
        # === SORT OPTIONS ===
        self.sort_dropdown = widgets.Dropdown(
            options=[
                ('Name', 'name'),
                ('Size', 'size'),
                ('Modified Date', 'date'),
                ('Type', 'type')
            ],
            value='name',
            description='Sort by:',
            layout=widgets.Layout(width='200px')
        )
        self.sort_dropdown.observe(self._on_sort_change, names='value')
        
        self.sort_order_btn = widgets.ToggleButton(
            value=False,
            description='â Ascending',
            button_style='',
            layout=widgets.Layout(width='110px')
        )
        self.sort_order_btn.observe(self._on_sort_order_change, names='value')
        
        self.sort_bar = widgets.HBox([
            self.sort_dropdown,
            self.sort_order_btn
        ], layout=widgets.Layout(margin='5px 0'))
        
        # === FILE LIST HEADER ===
        self.list_header = widgets.HTML(
            value=self._get_list_header_html()
        )
        
        # === FILE LIST ===
        self.file_list_output = widgets.Output(
            layout=widgets.Layout(
                border='1px solid #ddd',
                min_height='300px',
                max_height='500px',
                overflow_y='auto',
                padding='5px'
            )
        )
        
        # === STATUS BAR ===
        self.status_bar = widgets.HTML(
            value="<i>Ready</i>"
        )
        
        # === FILE INFO PANEL ===
        self.info_panel = widgets.HTML(
            value="<div style='padding: 10px; background: #f5f5f5; border-radius: 5px;'><i>Select a file to view details</i></div>"
        )
        
        # === MAIN LAYOUT ===
        self.main_container = widgets.VBox([
            self.title,
            widgets.HTML("<hr style='margin: 5px 0;'>"),
            self.nav_buttons,
            self.path_bar,
            self.breadcrumb,
            widgets.HTML("<hr style='margin: 5px 0;'>"),
            widgets.HBox([self.search_bar, widgets.HTML("&nbsp;&nbsp;&nbsp;"), self.sort_bar]),
            widgets.HTML("<hr style='margin: 5px 0;'>"),
            self.list_header,
            self.file_list_output,
            self.status_bar,
            widgets.HTML("<hr style='margin: 5px 0;'>"),
            widgets.HTML("<b>File Details:</b>"),
            self.info_panel
        ], layout=widgets.Layout(
            padding='15px',
            border='2px solid #1a73e8',
            border_radius='10px',
            width='100%',
            max_width='900px'
        ))
    
    def _get_list_header_html(self):
        """Generate the header row for the file list"""
        return """
        <div style='display: grid; grid-template-columns: 40px 1fr 100px 150px 100px; 
                    background: #e8e8e8; padding: 8px; font-weight: bold; border-radius: 5px;'>
            <span></span>
            <span>Name</span>
            <span>Size</span>
            <span>Modified</span>
            <span>Type</span>
        </div>
        """
    
    def _format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def _format_date(self, timestamp):
        """Format timestamp to readable date"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return "Unknown"
    
    def _get_file_icon(self, path, is_dir):
        """Get appropriate icon for file type"""
        if is_dir:
            return "ð"
        
        ext = Path(path).suffix.lower()
        
        icons = {
            '.py': 'ð',
            '.ipynb': 'ð',
            '.sql': 'ðï¸',
            '.txt': 'ð',
            '.md': 'ð',
            '.csv': 'ð',
            '.json': 'ð',
            '.xml': 'ð°',
            '.yaml': 'âï¸',
            '.yml': 'âï¸',
            '.parquet': 'ð¦',
            '.delta': 'ðº',
            '.jar': 'â',
            '.scala': 'ð·',
            '.r': 'ð',
            '.sh': 'ð»',
            '.html': 'ð',
            '.css': 'ð¨',
            '.js': 'â¡',
            '.png': 'ð¼ï¸',
            '.jpg': 'ð¼ï¸',
            '.jpeg': 'ð¼ï¸',
            '.gif': 'ð¼ï¸',
            '.pdf': 'ð',
            '.zip': 'ðï¸',
            '.tar': 'ðï¸',
            '.gz': 'ðï¸',
            '.log': 'ð',
        }
        
        return icons.get(ext, 'ð')
    
    def _get_file_type(self, path, is_dir):
        """Get file type description"""
        if is_dir:
            return "Folder"
        
        ext = Path(path).suffix.lower()
        
        types = {
            '.py': 'Python',
            '.ipynb': 'Notebook',
            '.sql': 'SQL',
            '.txt': 'Text',
            '.md': 'Markdown',
            '.csv': 'CSV',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.parquet': 'Parquet',
            '.delta': 'Delta',
            '.jar': 'JAR',
            '.scala': 'Scala',
            '.r': 'R Script',
            '.sh': 'Shell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.js': 'JavaScript',
            '.png': 'Image',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.gif': 'Image',
            '.pdf': 'PDF',
            '.zip': 'Archive',
            '.tar': 'Archive',
            '.gz': 'Archive',
            '.log': 'Log',
        }
        
        return types.get(ext, ext[1:].upper() if ext else 'File')
    
    def _get_items(self, path):
        """Get list of items in directory with metadata"""
        items = []
        
        try:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                
                try:
                    stat_info = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    
                    items.append({
                        'name': name,
                        'path': full_path,
                        'is_dir': is_dir,
                        'size': stat_info.st_size if not is_dir else 0,
                        'modified': stat_info.st_mtime,
                        'icon': self._get_file_icon(full_path, is_dir),
                        'type': self._get_file_type(full_path, is_dir)
                    })
                except (PermissionError, OSError):
                    items.append({
                        'name': name,
                        'path': full_path,
                        'is_dir': False,
                        'size': 0,
                        'modified': 0,
                        'icon': 'â ï¸',
                        'type': 'Unknown'
                    })
        except PermissionError:
            pass
        except Exception as e:
            pass
        
        return items
    
    def _filter_items(self, items):
        """Filter items based on search query"""
        if not self.search_query:
            return items
        
        query = self.search_query.lower()
        filtered = []
        
        for item in items:
            if query in item['name'].lower():
                filtered.append(item)
            elif fnmatch.fnmatch(item['name'].lower(), f"*{query}*"):
                filtered.append(item)
        
        return filtered
    
    def _sort_items(self, items):
        """Sort items based on current sort settings"""
        # Always show directories first
        dirs = [i for i in items if i['is_dir']]
        files = [i for i in items if not i['is_dir']]
        
        sort_key = {
            'name': lambda x: x['name'].lower(),
            'size': lambda x: x['size'],
            'date': lambda x: x['modified'],
            'type': lambda x: x['type'].lower()
        }.get(self.sort_by, lambda x: x['name'].lower())
        
        dirs.sort(key=sort_key, reverse=self.sort_reverse)
        files.sort(key=sort_key, reverse=self.sort_reverse)
        
        return dirs + files
    
    def _update_breadcrumb(self):
        """Update breadcrumb navigation"""
        parts = self.current_path.split(os.sep)
        breadcrumb_html = "<div style='padding: 5px; background: #f0f7ff; border-radius: 5px;'>"
        
        current = ""
        for i, part in enumerate(parts):
            if not part:
                part = "/"
                current = "/"
            else:
                current = os.path.join(current, part) if current != "/" else "/" + part
            
            if i < len(parts) - 1:
                breadcrumb_html += f"<a href='#' onclick='return false;' style='color: #1a73e8; text-decoration: none;'>{part}</a> / "
            else:
                breadcrumb_html += f"<b>{part}</b>"
        
        breadcrumb_html += "</div>"
        self.breadcrumb.value = breadcrumb_html
    
    def _update_nav_buttons(self):
        """Update navigation button states"""
        self.back_btn.disabled = self.history_index <= 0
        self.forward_btn.disabled = self.history_index >= len(self.history) - 1
    
    def _navigate_to(self, path, add_to_history=True):
        """Navigate to a directory"""
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            self.status_bar.value = f"<span style='color: red;'>â Path does not exist: {path}</span>"
            return
        
        if not os.path.isdir(path):
            # It's a file - show info but don't navigate
            self._show_file_info(path)
            return
        
        self.current_path = path
        self.path_input.value = path
        
        # Update history
        if add_to_history:
            # Remove forward history
            self.history = self.history[:self.history_index + 1]
            self.history.append(path)
            self.history_index = len(self.history) - 1
        
        self._update_nav_buttons()
        self._update_breadcrumb()
        self._refresh_file_list()
    
    def _refresh_file_list(self):
        """Refresh the file list display"""
        with self.file_list_output:
            clear_output(wait=True)
            
            items = self._get_items(self.current_path)
            items = self._filter_items(items)
            items = self._sort_items(items)
            
            if not items:
                if self.search_query:
                    display(HTML("<div style='padding: 20px; text-align: center; color: #666;'><i>No items match your search</i></div>"))
                else:
                    display(HTML("<div style='padding: 20px; text-align: center; color: #666;'><i>This folder is empty</i></div>"))
                self.status_bar.value = "0 items"
                return
            
            # Create clickable buttons for each item
            for item in items:
                self._create_item_row(item)
            
            # Update status
            dir_count = sum(1 for i in items if i['is_dir'])
            file_count = len(items) - dir_count
            total_size = sum(i['size'] for i in items if not i['is_dir'])
            
            status_text = f"{dir_count} folder(s), {file_count} file(s)"
            if total_size > 0:
                status_text += f" | Total: {self._format_size(total_size)}"
            if self.search_query:
                status_text += f" | Search: '{self.search_query}'"
            
            self.status_bar.value = status_text
    
    def _create_item_row(self, item):
        """Create a clickable row for an item"""
        # Item button
        btn = widgets.Button(
            description="",
            layout=widgets.Layout(width='100%', height='auto'),
            button_style=''
        )
        
        # Format the row content
        size_str = self._format_size(item['size']) if not item['is_dir'] else "--"
        date_str = self._format_date(item['modified'])
        
        row_html = f"""
        <div style='display: grid; grid-template-columns: 40px 1fr 100px 150px 100px; 
                    align-items: center; padding: 5px; width: 100%;'>
            <span style='font-size: 1.2em;'>{item['icon']}</span>
            <span style='overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
                  title='{item['name']}'>{item['name']}</span>
            <span style='color: #666;'>{size_str}</span>
            <span style='color: #666;'>{date_str}</span>
            <span style='color: #888;'>{item['type']}</span>
        </div>
        """
        
        btn_with_html = widgets.HTML(value=f"""
        <div style='display: grid; grid-template-columns: 40px 1fr 100px 150px 100px; 
                    align-items: center; padding: 8px; width: 100%; cursor: pointer;
                    border-radius: 5px; transition: background 0.2s;'
             onmouseover="this.style.background='#e3f2fd'"
             onmouseout="this.style.background='transparent'">
            <span style='font-size: 1.2em;'>{item['icon']}</span>
            <span style='overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
                  title='{item['name']}'><b>{item['name']}</b></span>
            <span style='color: #666;'>{size_str}</span>
            <span style='color: #666;'>{date_str}</span>
            <span style='color: #888;'>{item['type']}</span>
        </div>
        """)
        
        # Create a clickable button overlay
        item_btn = widgets.Button(
            description=f"{item['icon']} {item['name']}",
            layout=widgets.Layout(width='100%'),
            button_style='info' if item['is_dir'] else ''
        )
        
        # Store item data for click handler
        item_btn.item_data = item
        item_btn.on_click(self._on_item_click)
        
        # Create info row
        info_text = f"  ð {size_str}  |  ð {date_str}  |  ð {item['type']}"
        info_label = widgets.HTML(
            value=f"<span style='color: #666; font-size: 0.85em; margin-left: 35px;'>{info_text}</span>"
        )
        
        # Display as VBox
        item_container = widgets.VBox([
            item_btn,
            info_label
        ], layout=widgets.Layout(
            margin='2px 0',
            padding='2px',
            border='1px solid #eee',
            border_radius='5px'
        ))
        
        display(item_container)
    
    def _on_item_click(self, btn):
        """Handle item click"""
        item = btn.item_data
        
        if item['is_dir']:
            self._navigate_to(item['path'], add_to_history=True)
        else:
            self._show_file_info(item['path'])
    
    def _show_file_info(self, path):
        """Show detailed file information"""
        try:
            stat_info = os.stat(path)
            name = os.path.basename(path)
            is_dir = os.path.isdir(path)
            
            info_html = f"""
            <div style='padding: 15px; background: #f5f5f5; border-radius: 8px; border-left: 4px solid #1a73e8;'>
                <h3 style='margin: 0 0 10px 0;'>{self._get_file_icon(path, is_dir)} {name}</h3>
                <table style='width: 100%;'>
                    <tr><td><b>Full Path:</b></td><td style='word-break: break-all;'>{path}</td></tr>
                    <tr><td><b>Type:</b></td><td>{self._get_file_type(path, is_dir)}</td></tr>
                    <tr><td><b>Size:</b></td><td>{self._format_size(stat_info.st_size)} ({stat_info.st_size:,} bytes)</td></tr>
                    <tr><td><b>Modified:</b></td><td>{self._format_date(stat_info.st_mtime)}</td></tr>
                    <tr><td><b>Created:</b></td><td>{self._format_date(stat_info.st_ctime)}</td></tr>
                    <tr><td><b>Accessed:</b></td><td>{self._format_date(stat_info.st_atime)}</td></tr>
                    <tr><td><b>Permissions:</b></td><td>{oct(stat_info.st_mode)[-3:]}</td></tr>
                </table>
            </div>
            """
            
            self.info_panel.value = info_html
            
        except Exception as e:
            self.info_panel.value = f"<div style='color: red; padding: 10px;'>â Error reading file info: {str(e)}</div>"
    
    # === EVENT HANDLERS ===
    
    def _go_back(self, btn):
        """Go back in history"""
        if self.history_index > 0:
            self.history_index -= 1
            self._navigate_to(self.history[self.history_index], add_to_history=False)
    
    def _go_forward(self, btn):
        """Go forward in history"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._navigate_to(self.history[self.history_index], add_to_history=False)
    
    def _go_up(self, btn):
        """Go to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self._navigate_to(parent, add_to_history=True)
    
    def _go_home(self, btn):
        """Go to home directory"""
        home = os.path.expanduser("~")
        self._navigate_to(home, add_to_history=True)
    
    def _refresh(self, btn):
        """Refresh current directory"""
        self._refresh_file_list()
        self.status_bar.value = "ð Refreshed"
    
    def _on_path_submit(self, text):
        """Handle path input submission"""
        self._navigate_to(text.value, add_to_history=True)
    
    def _on_go_click(self, btn):
        """Handle Go button click"""
        self._navigate_to(self.path_input.value, add_to_history=True)
    
    def _on_search_change(self, change):
        """Handle search input change"""
        self.search_query = change['new']
        self._refresh_file_list()
    
    def _clear_search(self, btn):
        """Clear search"""
        self.search_input.value = ""
        self.search_query = ""
        self._refresh_file_list()
    
    def _on_sort_change(self, change):
        """Handle sort dropdown change"""
        self.sort_by = change['new']
        self._refresh_file_list()
    
    def _on_sort_order_change(self, change):
        """Handle sort order toggle"""
        self.sort_reverse = change['new']
        self.sort_order_btn.description = 'â Descending' if self.sort_reverse else 'â Ascending'
        self._refresh_file_list()
    
    def display(self):
        """Display the file explorer"""
        display(self.main_container)


# === LAUNCH THE FILE EXPLORER ===
# Uncomment and modify the start_path as needed for your Databricks environment

# Common starting paths for Databricks:
# - "/" for root
# - "/dbfs" for DBFS root
# - "/Workspace" for workspace files
# - os.getcwd() for current working directory

def launch_explorer(start_path=None):
    """
    Launch the file explorer.
    
    Args:
        start_path: Starting directory path. Defaults to current working directory.
    """
    if start_path is None:
        start_path = os.getcwd()
    
    explorer = DatabricksFileExplorer(start_path=start_path)
    explorer.display()
    return explorer

# Auto-launch when running in notebook
if __name__ == "__main__":
    print("Launching Databricks File Explorer...")
    print("=" * 50)
    explorer = launch_explorer()
