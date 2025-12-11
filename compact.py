# =============================================================================
# DATABRICKS FILE EXPLORER - QUICK START VERSION
# =============================================================================
# Simply copy this entire cell into a Databricks notebook and run it!
# The explorer will launch automatically at the bottom of the cell.
# =============================================================================

import os, ipywidgets as widgets
from IPython.display import display, clear_output, HTML
from datetime import datetime
from pathlib import Path
import fnmatch

class FileExplorer:
    def __init__(self, start_path="/"):
        self.history, self.history_index = [], -1
        self.current_path = start_path
        self.sort_by, self.sort_reverse, self.search_query = "name", False, ""
        self._build_ui()
        self._navigate_to(start_path, add_to_history=True)
    
    def _build_ui(self):
        # Navigation buttons
        self.back_btn = widgets.Button(description="◀ Back", disabled=True, button_style='info', layout=widgets.Layout(width='80px'))
        self.forward_btn = widgets.Button(description="▶ Fwd", disabled=True, button_style='info', layout=widgets.Layout(width='70px'))
        self.up_btn = widgets.Button(description="⬆ Up", button_style='warning', layout=widgets.Layout(width='60px'))
        self.home_btn = widgets.Button(description="🏠", button_style='success', layout=widgets.Layout(width='50px'))
        self.refresh_btn = widgets.Button(description="🔄", layout=widgets.Layout(width='50px'))
        
        self.back_btn.on_click(lambda b: self._go_back())
        self.forward_btn.on_click(lambda b: self._go_forward())
        self.up_btn.on_click(lambda b: self._go_up())
        self.home_btn.on_click(lambda b: self._navigate_to(os.path.expanduser("~"), True))
        self.refresh_btn.on_click(lambda b: self._refresh_file_list())
        
        # Path bar
        self.path_input = widgets.Text(value=self.current_path, layout=widgets.Layout(width='65%'))
        self.path_input.on_submit(lambda t: self._navigate_to(t.value, True))
        self.go_btn = widgets.Button(description="Go", button_style='primary', layout=widgets.Layout(width='50px'))
        self.go_btn.on_click(lambda b: self._navigate_to(self.path_input.value, True))
        
        # Search
        self.search_input = widgets.Text(placeholder='🔍 Search...', layout=widgets.Layout(width='200px'))
        self.search_input.observe(lambda c: self._on_search(c['new']), names='value')
        
        # Sort
        self.sort_dropdown = widgets.Dropdown(options=[('Name','name'),('Size','size'),('Date','date'),('Type','type')], value='name', layout=widgets.Layout(width='120px'))
        self.sort_dropdown.observe(lambda c: self._on_sort(c['new']), names='value')
        
        # File list & status
        self.file_output = widgets.Output(layout=widgets.Layout(border='1px solid #ccc', min_height='250px', max_height='400px', overflow_y='auto', padding='5px'))
        self.status = widgets.HTML(value="Ready")
        self.info_panel = widgets.HTML(value="<i>Select a file for details</i>")
        
        # Layout
        self.ui = widgets.VBox([
            widgets.HTML("<h3 style='color:#1a73e8;margin:0'>📁 File Explorer</h3>"),
            widgets.HBox([self.back_btn, self.forward_btn, self.up_btn, self.home_btn, self.refresh_btn]),
            widgets.HBox([widgets.HTML("<b>Path:</b>&nbsp;"), self.path_input, self.go_btn]),
            widgets.HBox([self.search_input, widgets.HTML("&nbsp;Sort:&nbsp;"), self.sort_dropdown]),
            widgets.HTML("<div style='background:#eee;padding:5px;font-weight:bold'>📄 Name | Size | Modified | Type</div>"),
            self.file_output, self.status,
            widgets.HTML("<b>Details:</b>"), self.info_panel
        ], layout=widgets.Layout(padding='10px', border='2px solid #1a73e8', border_radius='8px', max_width='800px'))
    
    def _fmt_size(self, b):
        for u in ['B','KB','MB','GB','TB']:
            if b < 1024: return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} PB"
    
    def _fmt_date(self, ts):
        try: return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except: return "Unknown"
    
    def _get_icon(self, p, is_dir):
        if is_dir: return "📁"
        ext = Path(p).suffix.lower()
        icons = {'.py':'🐍','.ipynb':'📓','.sql':'🗃️','.csv':'📊','.json':'📋','.parquet':'📦','.txt':'📄','.md':'📝','.sh':'💻','.jar':'☕','.scala':'🔷','.html':'🌐','.pdf':'📕','.zip':'🗜️','.png':'🖼️','.jpg':'🖼️'}
        return icons.get(ext, '📄')
    
    def _get_type(self, p, is_dir):
        if is_dir: return "Folder"
        ext = Path(p).suffix.lower()
        types = {'.py':'Python','.ipynb':'Notebook','.sql':'SQL','.csv':'CSV','.json':'JSON','.parquet':'Parquet','.txt':'Text','.md':'Markdown','.html':'HTML','.pdf':'PDF','.zip':'Archive'}
        return types.get(ext, ext[1:].upper() if ext else 'File')
    
    def _get_items(self, path):
        items = []
        try:
            for name in os.listdir(path):
                fp = os.path.join(path, name)
                try:
                    st = os.stat(fp)
                    is_dir = os.path.isdir(fp)
                    items.append({'name':name,'path':fp,'is_dir':is_dir,'size':st.st_size if not is_dir else 0,'modified':st.st_mtime,'icon':self._get_icon(fp,is_dir),'type':self._get_type(fp,is_dir)})
                except: items.append({'name':name,'path':fp,'is_dir':False,'size':0,'modified':0,'icon':'⚠️','type':'Unknown'})
        except: pass
        return items
    
    def _filter_sort(self, items):
        if self.search_query:
            items = [i for i in items if self.search_query.lower() in i['name'].lower()]
        dirs = sorted([i for i in items if i['is_dir']], key=lambda x: x[self.sort_by] if self.sort_by != 'name' else x['name'].lower(), reverse=self.sort_reverse)
        files = sorted([i for i in items if not i['is_dir']], key=lambda x: x[self.sort_by] if self.sort_by != 'name' else x['name'].lower(), reverse=self.sort_reverse)
        return dirs + files
    
    def _navigate_to(self, path, add_hist=True):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            self.status.value = f"<span style='color:red'>❌ Path not found: {path}</span>"
            return
        if not os.path.isdir(path):
            self._show_info(path)
            return
        self.current_path = path
        self.path_input.value = path
        if add_hist:
            self.history = self.history[:self.history_index+1] + [path]
            self.history_index = len(self.history) - 1
        self._update_nav()
        self._refresh_file_list()
    
    def _update_nav(self):
        self.back_btn.disabled = self.history_index <= 0
        self.forward_btn.disabled = self.history_index >= len(self.history) - 1
    
    def _refresh_file_list(self):
        with self.file_output:
            clear_output(wait=True)
            items = self._filter_sort(self._get_items(self.current_path))
            if not items:
                display(HTML("<div style='padding:20px;text-align:center;color:#666'><i>Empty or no matches</i></div>"))
                self.status.value = "0 items"
                return
            for item in items:
                btn = widgets.Button(description=f"{item['icon']} {item['name']}", layout=widgets.Layout(width='100%'), button_style='info' if item['is_dir'] else '')
                btn.item = item
                btn.on_click(self._on_item_click)
                meta = f"  {self._fmt_size(item['size']) if not item['is_dir'] else '--'} | {self._fmt_date(item['modified'])} | {item['type']}"
                display(widgets.VBox([btn, widgets.HTML(f"<span style='color:#666;font-size:0.8em;margin-left:20px'>{meta}</span>")], layout=widgets.Layout(margin='2px 0', border='1px solid #eee', border_radius='4px')))
            self.status.value = f"{sum(1 for i in items if i['is_dir'])} folders, {sum(1 for i in items if not i['is_dir'])} files"
    
    def _on_item_click(self, btn):
        if btn.item['is_dir']: self._navigate_to(btn.item['path'], True)
        else: self._show_info(btn.item['path'])
    
    def _show_info(self, path):
        try:
            st = os.stat(path)
            name = os.path.basename(path)
            is_dir = os.path.isdir(path)
            self.info_panel.value = f"""<div style='padding:10px;background:#f5f5f5;border-radius:5px;border-left:3px solid #1a73e8'>
                <b>{self._get_icon(path,is_dir)} {name}</b><br>
                <small><b>Path:</b> {path}<br><b>Size:</b> {self._fmt_size(st.st_size)} ({st.st_size:,} bytes)<br>
                <b>Modified:</b> {self._fmt_date(st.st_mtime)}<br><b>Type:</b> {self._get_type(path,is_dir)}</small></div>"""
        except Exception as e:
            self.info_panel.value = f"<span style='color:red'>Error: {e}</span>"
    
    def _go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self._navigate_to(self.history[self.history_index], False)
    
    def _go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._navigate_to(self.history[self.history_index], False)
    
    def _go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path: self._navigate_to(parent, True)
    
    def _on_search(self, q):
        self.search_query = q
        self._refresh_file_list()
    
    def _on_sort(self, s):
        self.sort_by = s
        self._refresh_file_list()
    
    def show(self): display(self.ui)

# =============================================================================
# LAUNCH THE EXPLORER
# =============================================================================
# Change start_path to your preferred starting location:
# - "/" for root
# - "/dbfs" for DBFS
# - "/Workspace" for workspace files  
# - os.getcwd() for current directory

explorer = FileExplorer(start_path=os.getcwd())
explorer.show()
