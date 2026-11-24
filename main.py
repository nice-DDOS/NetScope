"""NetScope desktop utility: classic ttk GUI, bilingual labels, fixed technical values."""
import csv
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import network as net
import storage

PREFS = Path.home() / '.netscope' / 'preferences.json'
AR = {
    'Overview':'نظرة عامة', 'IP Analyzer':'تحليل IP', 'DNS Lookup':'استعلام DNS',
    'TCP Laboratory':'مختبر TCP', 'Activity History':'سجل النشاط', 'Help':'المساعدة',
    'Language':'اللغة', 'Appearance':'المظهر', 'Light':'فاتح', 'Dark':'داكن',
    'Ready':'جاهز', 'Working…':'جارٍ التنفيذ…', 'Completed':'اكتملت العملية',
    'Failed':'فشلت العملية', 'Input':'الإدخال', 'Results':'النتائج',
    'IP address':'عنوان IP', 'Hostname':'اسم المضيف', 'Analyze':'تحليل',
    'Online IP info':'معلومات IP عبر الإنترنت', 'My device':'جهازي',
    'Resolve':'استعلام', 'Copy results':'نسخ النتائج', 'Clear':'مسح',
    'Property':'الخاصية', 'Value':'القيمة', 'Version':'الإصدار',
    'Classification':'التصنيف', 'Global':'عام', 'Loopback':'حلقة محلية',
    'Private flag':'مؤشر الخصوصية', 'Addresses':'العناوين',
    'Resolved local addresses':'العناوين المحلية', 'Country (approx.)':'الدولة (تقريبي)',
    'Region (approx.)':'المنطقة (تقريبي)', 'Network / ISP':'مزود الشبكة',
    'Timezone (approx.)':'المنطقة الزمنية (تقريبي)', 'Source':'المصدر',
    'Note':'ملاحظة', 'Server':'الخادم', 'Address':'العنوان', 'Protocol':'البروتوكول',
    'Target':'الهدف', 'Sent':'المرسل', 'Received':'المستلم', 'Match':'التطابق',
    'Elapsed (connect + echo)':'المدة (اتصال وصدى)', 'Port':'المنفذ',
    'Message':'الرسالة', 'Start server':'تشغيل الخادم', 'Send echo':'إرسال صدى',
    'Stop server':'إيقاف الخادم', 'First port':'أول منفذ', 'Last port':'آخر منفذ',
    'Check local ports':'فحص المنافذ المحلية', 'Refresh':'تحديث', 'Export CSV':'تصدير CSV',
    'Clear history':'مسح السجل', 'Time':'الوقت', 'Action':'العملية',
    'Status':'الحالة', 'Summary':'الملخص', 'Quick access':'وصول سريع',
    'Network programming utilities':'أدوات برمجة الشبكات',
    'Validate an IPv4 or IPv6 address.':'تحقق من صحة عنوان IPv4 أو IPv6.',
    'Resolve a hostname using the system DNS resolver.':'تحويل اسم المضيف إلى عنوان باستخدام DNS.',
    'Local TCP only: 127.0.0.1. Start the server, then send a message.':'اتصال محلي فقط: شغّل الخادم ثم أرسل رسالة.',
    'Local SQLite activity log; IPs and messages are not saved.':'سجل SQLite محلي؛ لا تُحفظ العناوين والرسائل.',
    'Download the source and run python main.py.':'حمّل الكود وشغّل python main.py.',
    'Online lookup sends the entered IP to ipapi.co. Continue?':'سيُرسل عنوان IP المدخل إلى ipapi.co. هل تتابع؟',
    'Delete local activity records?':'حذف سجلات النشاط المحلية؟',
    'Wait until the current operation finishes.':'انتظر اكتمال العملية الحالية.',
    'Operation completed':'اكتملت العملية', 'Operation failed':'فشلت العملية',
    'IP validation':'التحقق من IP', 'Public IP metadata':'معلومات IP العامة',
    'Local identity':'هوية الجهاز', 'TCP echo':'صدى TCP', 'Local port check':'فحص منفذ محلي',
    'Copied':'تم النسخ', 'CSV exported':'تم التصدير', 'Error':'خطأ',
    'Online IP information is approximate.':'معلومات IP عبر الإنترنت تقريبية.',
    'Local mode':'وضع محلي', 'Run':'تشغيل', 'Maximum 32 local ports.':'حد أقصى 32 منفذاً محلياً.'
}
PALETTES = {
    'light': dict(bg='#e7edf4', panel='#ffffff', ink='#142b43', muted='#53677e',
                  border='#9eafc1', button='#dce6ef', selected='#d3e8fd', accent='#23649b'),
    'dark': dict(bg='#202a35', panel='#2a3644', ink='#edf3fa', muted='#b6c5d4',
                 border='#53667a', button='#3b4e62', selected='#395a79', accent='#9ccaff')
}
PAGES = ('Overview','IP Analyzer','DNS Lookup','TCP Laboratory','Activity History','Help')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('NetScope — Network Utilities')
        self.geometry('1000x680')
        self.minsize(840, 570)
        self.lang = tk.StringVar(value='English')
        self.theme = tk.StringVar(value='Light')
        try:
            p = json.loads(PREFS.read_text(encoding='utf-8'))
            if p.get('lang') in ('English','العربية'): self.lang.set(p['lang'])
            if p.get('theme') in ('Light','Dark'): self.theme.set(p['theme'])
        except (OSError, ValueError):
            pass
        self.fields = {k:tk.StringVar(value=v) for k,v in
                       {'ip':'8.8.8.8','host':'localhost','port':'9999','message':'Hello Network!',
                        'first':'9998','last':'10000'}.items()}
        self.page = 'Overview'
        self.outputs = {}
        self.jobs = queue.Queue()
        self.server = net.EchoServer()
        self.busy = False
        self.status_key = 'Ready'
        self.status = tk.StringVar()
        storage.init_db()
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.build()
        self.after(80, self.poll)
        self.protocol('WM_DELETE_WINDOW',self.close_app)

    def tr(self, value):
        return AR.get(value, value) if self.lang.get() == 'العربية' else value

    def save_preferences(self):
        try:
            PREFS.parent.mkdir(parents=True, exist_ok=True)
            PREFS.write_text(json.dumps({'lang':self.lang.get(),'theme':self.theme.get()},ensure_ascii=False),encoding='utf-8')
        except OSError:
            pass

    def appearance(self, *_):
        self.save_preferences()
        self.build()

    def style_ui(self):
        c=PALETTES[self.theme.get().lower()]
        self.configure(bg=c['bg'])
        s=self.style
        s.configure('.',font=('Segoe UI',10),background=c['bg'],foreground=c['ink'],
                    bordercolor=c['border'],lightcolor=c['border'],darkcolor=c['border'])
        s.configure('TFrame',background=c['bg'])
        s.configure('TLabel',background=c['bg'],foreground=c['ink'])
        s.configure('Heading.TLabel',font=('Segoe UI',19),foreground=c['accent'])
        s.configure('Muted.TLabel',foreground=c['muted'])
        s.configure('TButton',padding=(10,6),background=c['button'],relief='raised')
        s.map('TButton',background=[('active',c['selected']),('disabled',c['bg'])])
        s.configure('Selected.TButton',background=c['selected'])
        s.configure('TEntry',fieldbackground=c['panel'],foreground=c['ink'],padding=5)
        s.configure('TCombobox',fieldbackground=c['panel'],foreground=c['ink'],padding=3)
        s.map('TCombobox',fieldbackground=[('readonly',c['panel'])],foreground=[('readonly',c['ink'])])
        s.configure('Treeview',background=c['panel'],fieldbackground=c['panel'],foreground=c['ink'],rowheight=28)
        s.configure('Treeview.Heading',background=c['button'],foreground=c['ink'],relief='raised')
        s.map('Treeview',background=[('selected',c['selected'])],foreground=[('selected',c['ink'])])
        s.configure('TLabelframe',background=c['bg'])
        s.configure('TLabelframe.Label',background=c['bg'],foreground=c['accent'])

    def build(self):
        for w in self.winfo_children(): w.destroy()
        self.style_ui()
        self.action_buttons=[]
        outer=ttk.Frame(self,padding=8);outer.pack(fill='both',expand=True)
        bar=ttk.Frame(outer);bar.pack(fill='x')
        ttk.Label(bar,text='NetScope',font=('Segoe UI',16,'bold')).pack(side='left',padx=6)
        for label,var,vals in [('Appearance',self.theme,('Light','Dark')),('Language',self.lang,('English','العربية'))]:
            cb=ttk.Combobox(bar,textvariable=var,values=vals,state='readonly',width=10)
            cb.pack(side='right',padx=5,pady=5)
            cb.bind('<<ComboboxSelected>>',self.appearance)
            ttk.Label(bar,text=self.tr(label)).pack(side='right')
        ttk.Separator(outer).pack(fill='x',pady=6)
        workspace=ttk.Frame(outer);workspace.pack(fill='both',expand=True)
        nav=ttk.Frame(workspace,width=180,padding=(0,4,8,0));nav.pack(side='left',fill='y');nav.pack_propagate(False)
        for p in PAGES:
            ttk.Button(nav,text=self.tr(p),style='Selected.TButton' if p==self.page else 'TButton',
                       command=lambda p=p:self.navigate(p)).pack(fill='x',pady=3)
        ttk.Separator(workspace,orient='vertical').pack(side='left',fill='y')
        self.body=ttk.Frame(workspace,padding=14);self.body.pack(side='left',fill='both',expand=True)
        ttk.Label(self.body,text=self.tr(self.page),style='Heading.TLabel').pack(anchor=self.anchor())
        self.build_page()
        ttk.Separator(outer).pack(fill='x',pady=5)
        self.status.set(self.tr(self.status_key))
        ttk.Label(outer,textvariable=self.status).pack(side='left',padx=6)
        ttk.Label(outer,text='NetScope 2.0 | 127.0.0.1',style='Muted.TLabel').pack(side='right')
        self.update_buttons()

    def anchor(self):
        return 'e' if self.lang.get()=='العربية' else 'w'

    def navigate(self,page):
        self.page=page
        self.build()

    def hint(self,text,parent=None):
        ttk.Label(parent or self.body,text=self.tr(text),style='Muted.TLabel',wraplength=580,
                  justify='right' if self.lang.get()=='العربية' else 'left').pack(anchor=self.anchor(),pady=5)

    def group(self,name):
        f=ttk.LabelFrame(self.body,text=self.tr(name),padding=10)
        f.pack(fill='x',pady=8)
        return f

    def field(self,parent,label,key,width=24):
        f=ttk.Frame(parent);f.pack(side='left',padx=(0,10),pady=4,fill='x',expand=True)
        ttk.Label(f,text=self.tr(label)).pack(anchor=self.anchor())
        e=ttk.Entry(f,textvariable=self.fields[key],width=width,justify='left')
        e.pack(fill='x',pady=(3,0))
        return e

    def button(self,parent,label,fn,job=False):
        b=ttk.Button(parent,text=self.tr(label),command=fn);b.pack(side='left',padx=(0,6),pady=4)
        if job:self.action_buttons.append(b)
        return b

    def actions(self,parent):
        f=ttk.Frame(parent);f.pack(fill='x',pady=3);return f

    def build_page(self):
        p=self.page
        if p=='Overview':
            self.hint('Network programming utilities')
            g=self.group('Quick access')
            for target in PAGES[1:]:
                ttk.Button(g,text=self.tr(target),command=lambda p=target:self.navigate(p)).pack(fill='x',pady=4)
        elif p=='IP Analyzer':
            self.hint('Validate an IPv4 or IPv6 address.')
            g=self.group('Input')
            row=self.actions(g);entry=self.field(row,'IP address','ip')
            row=self.actions(g)
            run=lambda:self.run(p,'IP validation',net.inspect_ip,self.fields['ip'].get())
            self.button(row,'Analyze',run,True)
            self.button(row,'Online IP info',self.online,True)
            self.button(row,'My device',lambda:self.run(p,'Local identity',net.local_identity),True)
            entry.bind('<Return>',lambda _:run())
            self.hint('Online IP information is approximate.')
            self.result_table()
        elif p=='DNS Lookup':
            self.hint('Resolve a hostname using the system DNS resolver.')
            g=self.group('Input');row=self.actions(g);entry=self.field(row,'Hostname','host')
            run=lambda:self.run(p,'DNS Lookup',net.resolve_dns,self.fields['host'].get())
            self.button(self.actions(g),'Resolve',run,True);entry.bind('<Return>',lambda _:run())
            self.result_table()
        elif p=='TCP Laboratory':
            self.hint('Local TCP only: 127.0.0.1. Start the server, then send a message.')
            g=self.group('Server');row=self.actions(g)
            self.field(row,'Port','port',8);self.field(row,'Message','message')
            row=self.actions(g)
            self.button(row,'Start server',lambda:self.run(p,'Start server',self.server.start,self.fields['port'].get()),True)
            self.button(row,'Send echo',lambda:self.run(p,'TCP echo',net.echo_test,self.fields['port'].get(),self.fields['message'].get()),True)
            self.button(row,'Stop server',lambda:self.run(p,'Stop server',self.server.stop),True)
            g=self.group('Maximum 32 local ports.');row=self.actions(g)
            self.field(row,'First port','first',8);self.field(row,'Last port','last',8)
            self.button(self.actions(g),'Check local ports',lambda:self.run(p,'Local port check',net.check_local_ports,self.fields['first'].get(),self.fields['last'].get()),True)
            self.result_table()
        elif p=='Activity History':
            self.hint('Local SQLite activity log; IPs and messages are not saved.')
            row=self.actions(self.body)
            self.button(row,'Refresh',self.refresh_history)
            self.button(row,'Export CSV',self.export)
            self.button(row,'Clear history',self.clear_history)
            self.table=self.tree(self.body,('Time','Action','Status','Summary'),(150,150,70,180))
            self.refresh_history()
        else:
            self.hint('Download the source and run python main.py.')
            self.hint('Validate an IPv4 or IPv6 address.')
            self.hint('Resolve a hostname using the system DNS resolver.')
            self.hint('Local TCP only: 127.0.0.1. Start the server, then send a message.')
            self.hint('Local SQLite activity log; IPs and messages are not saved.')

    def tree(self,parent,cols,widths):
        f=ttk.Frame(parent);f.pack(fill='both',expand=True,pady=5)
        t=ttk.Treeview(f,columns=cols,show='headings',height=5)
        for col,width in zip(cols,widths):
            t.heading(col,text=self.tr(col));t.column(col,width=width,minwidth=50,anchor='w')
        y=ttk.Scrollbar(f,orient='vertical',command=t.yview)
        x=ttk.Scrollbar(f,orient='horizontal',command=t.xview)
        t.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        x.pack(side='bottom',fill='x');y.pack(side='right',fill='y');t.pack(fill='both',expand=True)
        return t

    def result_table(self):
        row=self.actions(self.body)
        self.button(row,'Copy results',self.copy)
        self.button(row,'Clear',self.clear_output)
        self.table=self.tree(self.body,('Property','Value'),(175,400))
        self.refresh_results()

    def refresh_results(self):
        self.table.delete(*self.table.get_children())
        for k,v in self.outputs.get(self.page,{}).items():
            parts=str(v).splitlines() or ['']
            for i,line in enumerate(parts):
                self.table.insert('','end',values=(self.tr(k) if i==0 else '',line))

    def set_status(self,k):
        self.status_key=k;self.status.set(self.tr(k))

    def clear_output(self):
        self.outputs.pop(self.page,None);self.refresh_results()

    def copy(self):
        result=self.outputs.get(self.page,{})
        self.clipboard_clear()
        self.clipboard_append('\n'.join(f'{k}: {v}' for k,v in result.items()))
        self.set_status('Copied')

    def online(self):
        if not self.busy and messagebox.askyesno('NetScope',self.tr('Online lookup sends the entered IP to ipapi.co. Continue?')):
            self.run(self.page,'Public IP metadata',net.public_metadata,self.fields['ip'].get())

    def update_buttons(self):
        for b in self.action_buttons:
            b.state(['disabled'] if self.busy else ['!disabled'])

    def run(self,page,action,fn,*args):
        if self.busy:return
        self.busy=True;self.set_status('Working…');self.update_buttons()
        def worker():
            try:self.jobs.put((page,action,fn(*args),False))
            except Exception as e:self.jobs.put((page,action,{'Error':f'{type(e).__name__}: {e}'},True))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        try:page,action,result,failed=self.jobs.get_nowait()
        except queue.Empty:pass
        else:
            self.outputs[page]=result
            self.busy=False;self.update_buttons()
            self.set_status('Failed' if failed else 'Completed')
            try:storage.save_event(action,'ERROR' if failed else 'OK','Operation failed' if failed else 'Operation completed')
            except OSError:pass
            if self.page==page:self.refresh_results()
            elif self.page=='Activity History':self.refresh_history()
        self.after(80,self.poll)

    def refresh_history(self):
        self.table.delete(*self.table.get_children())
        for t,a,s,d in storage.read_events():self.table.insert('','end',values=(t,self.tr(a),s,self.tr(d)))

    def clear_history(self):
        if messagebox.askyesno('NetScope',self.tr('Delete local activity records?')):
            storage.clear_events();self.refresh_history()

    def export(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if path:
            try:
                with open(path,'w',encoding='utf-8-sig',newline='') as f:
                    w=csv.writer(f);w.writerow(['Time','Action','Status','Summary']);w.writerows(storage.read_events())
                self.set_status('CSV exported')
            except OSError as e:messagebox.showerror('NetScope',str(e))

    def close_app(self):
        if self.busy:
            messagebox.showinfo('NetScope',self.tr('Wait until the current operation finishes.'));return
        self.server.stop();self.destroy()


if __name__=='__main__':
    App().mainloop()
