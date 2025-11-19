import tkinter as tk
from tkinter import Toplevel, messagebox, simpledialog
import sympy as sp
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from CoefIndet import CoefIndet

COLOR_FONDO = "#1e1e1e"
COLOR_PANEL = "#252526"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SEC = "#aaaaaa"
COLOR_INPUT = "#3c3c3c"
COLOR_BOTON = "#4CAF50"
COLOR_BOTON_SEC = "#007acc"
COLOR_BOTON_ACTUALIZAR = "#e09f3e" 

FUENTE_TITULO = ("Segoe UI", 18, "bold")
FUENTE_NORMAL = ("Segoe UI", 10)
FUENTE_MONO = ("Consolas", 10)

class Interfaz:
    def __init__(self):
        self.solver = None
        self.valores_iniciales = {}
        self.orden_ecuacion = None 
        self.entries_condiciones_variacion = []
        self.ultimo_metodo_exitoso = None 

        self.ventana = tk.Tk()
        self.ventana.title("Solver Ecuaciones Diferenciales - Dark Mode")
        self.ventana.geometry("1200x800")
        self.ventana.configure(bg=COLOR_FONDO)

        # --- LAYOUT PRINCIPAL ---
        self.panel_izquierdo = tk.Frame(self.ventana, bg=COLOR_FONDO, padx=20, pady=20)
        self.panel_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.panel_derecho = tk.Frame(self.ventana, bg=COLOR_PANEL, padx=10, pady=10)
        self.panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.panel_izquierdo, text="Resolución de EDOs", font=FUENTE_TITULO, 
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w", pady=(0, 20))

        tk.Label(self.panel_izquierdo, text="Ingrese la ecuación diferencial:", 
                 font=FUENTE_NORMAL, bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC).pack(anchor="w")
        
        self.entrada_ecuacion = tk.Entry(self.panel_izquierdo, font=FUENTE_NORMAL, 
                                         bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white",
                                         relief="flat", highlightthickness=1, highlightbackground="#555")
        self.entrada_ecuacion.pack(fill="x", pady=(5, 15), ipady=5)

        # Radiobuttons
        self.metodo = tk.StringVar(value="variacion")
        frame_radios = tk.Frame(self.panel_izquierdo, bg=COLOR_FONDO)
        frame_radios.pack(anchor="w", pady=5)
        estilo_radio = {'bg': COLOR_FONDO, 'fg': COLOR_TEXTO, 'selectcolor': COLOR_PANEL, 'activebackground': COLOR_FONDO, 'font': FUENTE_NORMAL}
        tk.Radiobutton(frame_radios, text="Variación de Parámetros", variable=self.metodo, 
                       value="variacion", command=self.limpiar_interfaz_variacion, **estilo_radio).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(frame_radios, text="Coeficientes Indeterminados", variable=self.metodo, 
                       value="indeterminados", command=self.limpiar_interfaz_variacion, **estilo_radio).pack(side=tk.LEFT)

        # Botones Resolver
        frame_botones = tk.Frame(self.panel_izquierdo, bg=COLOR_FONDO)
        frame_botones.pack(fill="x", pady=20)
        self.btn_resolver = tk.Button(frame_botones, text="RESOLVER", font=("Segoe UI", 10, "bold"),
                                      bg=COLOR_BOTON, fg="white", relief="flat", cursor="hand2",
                                      command=self.resolver_ecuacion)
        self.btn_resolver.pack(side=tk.LEFT, fill="x", expand=True, ipady=5, padx=(0, 5))
        self.btn_valores_antiguo = tk.Button(frame_botones, text="Valores Iniciales (Coef.)", font=FUENTE_NORMAL,
                                           bg=COLOR_INPUT, fg=COLOR_TEXTO, relief="flat", cursor="hand2",
                                           command=self.abrir_valores_iniciales)
        self.btn_valores_antiguo.pack(side=tk.LEFT, fill="x", expand=True, ipady=5, padx=(5, 0))

        # Resultados Text Area
        tk.Label(self.panel_izquierdo, text="Resultados:", font=FUENTE_NORMAL, bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC).pack(anchor="w")
        self.etiqueta_resultado = tk.Text(self.panel_izquierdo, font=FUENTE_MONO, 
                                          bg=COLOR_PANEL, fg=COLOR_TEXTO, relief="flat", height=15)
        self.etiqueta_resultado.pack(fill="both", expand=True, pady=5)

        # Frame Variación
        self.frame_variacion = tk.LabelFrame(self.panel_izquierdo, text="Condiciones Iniciales (Variación)", 
                                             font=FUENTE_NORMAL, bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC, bd=1, relief="solid")
        self.frame_variacion.pack(fill="x", pady=10)
        
        self.btn_aplicar_variacion = tk.Button(self.frame_variacion, text="Aplicar Condiciones y Graficar", 
                                               font=FUENTE_NORMAL, bg=COLOR_BOTON_SEC, fg="white", relief="flat",
                                               command=self.aplicar_condiciones_variacion, state=tk.DISABLED)
        self.btn_aplicar_variacion.pack(side=tk.BOTTOM, fill="x", padx=10, pady=10)

        # --- BARRA DE HERRAMIENTAS GRÁFICA 
        self.frame_controles_grafica = tk.Frame(self.panel_derecho, bg=COLOR_PANEL)
        self.frame_controles_grafica.pack(fill="x", pady=(0, 10))

        # Input X Min
        tk.Label(self.frame_controles_grafica, text="X Min:", bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side=tk.LEFT, padx=5)
        self.entry_xmin = tk.Entry(self.frame_controles_grafica, width=5, bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white", relief="flat")
        self.entry_xmin.insert(0, "-10")
        self.entry_xmin.pack(side=tk.LEFT, padx=5)

        # Input X Max
        tk.Label(self.frame_controles_grafica, text="X Max:", bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side=tk.LEFT, padx=5)
        self.entry_xmax = tk.Entry(self.frame_controles_grafica, width=5, bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white", relief="flat")
        self.entry_xmax.insert(0, "10")
        self.entry_xmax.pack(side=tk.LEFT, padx=5)

        # Botón Actualizar Gráfica
        self.btn_actualizar_grafica = tk.Button(self.frame_controles_grafica, text="🔄 Actualizar Gráfica", 
                                                bg=COLOR_BOTON_ACTUALIZAR, fg="white", relief="flat", cursor="hand2",
                                                command=self.actualizar_grafica_manual)
        self.btn_actualizar_grafica.pack(side=tk.RIGHT, padx=5)

        # --- CANVAS ---
        self.canvas = None
        self.limpiar_interfaz_variacion()
        self.ventana.mainloop()

    def limpiar_interfaz_variacion(self):
        for widget in self.frame_variacion.winfo_children():
            if widget != self.btn_aplicar_variacion: widget.destroy()
        self.entries_condiciones_variacion = []
        self.btn_aplicar_variacion.config(state=tk.DISABLED, bg="#555")
        
        # Limpiar gráfica también al cambiar método
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        self.ultimo_metodo_exitoso = None

        if self.metodo.get() == "variacion":
            self.btn_valores_antiguo.config(state=tk.DISABLED, bg="#333", fg="#777")
            self.frame_variacion.pack(fill="x", pady=10)
        else:
            self.btn_valores_antiguo.config(state=tk.NORMAL, bg=COLOR_INPUT, fg=COLOR_TEXTO)
            self.frame_variacion.pack_forget()

    def abrir_valores_iniciales(self):
        if self.metodo.get() == "variacion": return
        if not self.solver or self.orden_ecuacion is None:
            messagebox.showerror("Error", "Primero resuelva la ecuación.")
            return

        ventana_vi = Toplevel(self.ventana)
        ventana_vi.title("Valores Iniciales")
        ventana_vi.configure(bg=COLOR_FONDO)
        ventana_vi.geometry("300x" + str(self.orden_ecuacion * 60 + 80))

        tk.Label(ventana_vi, text=f"Ingrese {self.orden_ecuacion} valores:", font=FUENTE_NORMAL, bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)
        entradas = []
        for i in range(self.orden_ecuacion):
            frame_row = tk.Frame(ventana_vi, bg=COLOR_FONDO)
            frame_row.pack(pady=2)
            tk.Label(frame_row, text=f"y^{i}(0) = ", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side=tk.LEFT)
            entrada = tk.Entry(frame_row, bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white")
            entrada.pack(side=tk.LEFT)
            entradas.append(entrada)

        def guardar():
            try:
                self.valores_iniciales.clear()
                for i, entrada in enumerate(entradas):
                    v = entrada.get().strip()
                    if v: self.valores_iniciales[f'cond_{i}'] = float(v)
                messagebox.showinfo("Guardado", "Condiciones guardadas.")
                ventana_vi.destroy()
            except ValueError: messagebox.showerror("Error", "Números inválidos")

        tk.Button(ventana_vi, text="Guardar", bg=COLOR_BOTON, fg="white", relief="flat", command=guardar).pack(pady=10)

    def resolver_ecuacion(self):
        ecuacion = self.entrada_ecuacion.get().strip()
        if not ecuacion:
            messagebox.showerror("Error", "Ingrese una ecuación.")
            return

        self.etiqueta_resultado.delete("1.0", tk.END)
        
        # --- VARIACIÓN DE PARÁMETROS ---
        if self.metodo.get() == "variacion":
            try:
                for widget in self.frame_variacion.winfo_children():
                    if widget != self.btn_aplicar_variacion: widget.destroy()
                self.entries_condiciones_variacion = []
                
                from MetodoVariacionParametros import EDOSolver
                self.solver = EDOSolver(ecuacion)
                self.solver.resolver_homogenea()
                self.solver.resolver_particular()
                self.solver.crear_solucion_general()
                self.orden_ecuacion = self.solver.grado

                msg = "=== MÉTODO VARIACIÓN DE PARÁMETROS ===\n\n"
                msg += f"1. Raíces:\n{self.solver.raices}\n\n"
                msg += f"2. CFS:\n{sp.pretty(self.solver.CFS)}\n\n"
                msg += f"3. Homogénea (yh):\n{sp.pretty(self.solver.solucionHomogenea)}\n\n"
                msg += f"4. Integrales (u):\n{sp.pretty(self.solver.matriz_U_integrada)}\n\n"
                msg += f"5. Particular (yp):\n{sp.pretty(self.solver.y_p)}\n\n"
                msg += f"--- SOLUCIÓN GENERAL ---\n{sp.pretty(self.solver.get_solucion_general())}\n"
                
                self.etiqueta_resultado.insert(tk.END, msg)
                self.crear_inputs_variacion(self.orden_ecuacion)
                self.btn_aplicar_variacion.config(state=tk.NORMAL, bg=COLOR_BOTON_SEC)
                
                self.ultimo_metodo_exitoso = "variacion"
                # Graficar automáticamente la general (usando rangos de los inputs)
                self.actualizar_grafica_manual()

            except Exception as e:
                messagebox.showerror("Error Variación", str(e))

        # --- COEFICIENTES INDETERMINADOS ---
        else:
            try:
                self.solver = CoefIndet(ecuacion)
                self.etiqueta_resultado.insert(tk.END, "Resolviendo por Coeficientes Indeterminados...\n")
                self.solver.resolver()
                self.orden_ecuacion = self.solver.orden

                # Aplicar condiciones guardadas con el formato correcto
                if self.valores_iniciales:
                    ci_list = []
                    # Iterar ordenadamente para asignar las derivadas correctas
                    for key in sorted(self.valores_iniciales.keys()):
                        indice = int(key.split('_')[1])
                        valor = self.valores_iniciales[key]
                        
                        # Construir string con los apostrofes correctos
                        apostrofes = "'" * indice
                        ci_str = f"y{apostrofes}(0)={valor}"
                        ci_list.append(ci_str)
                    
                    self.solver.agregar_CI(ci_list)
                    self.solver.resolver()

                self.etiqueta_resultado.insert(tk.END, "\nSolución:\n" + self.solver.mostrar_sol() + "\n")
                
                self.ultimo_metodo_exitoso = "coeficientes"
                
                # Graficar automáticamente usando los inputs del panel derecho
                self.actualizar_grafica_manual()

            except Exception as e:
                messagebox.showerror("Error Coeficientes", str(e))

    def crear_inputs_variacion(self, n):
        frame_inputs = tk.Frame(self.frame_variacion, bg=COLOR_FONDO)
        frame_inputs.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_inputs, text=f"Ingrese {n} condiciones (ej: y'(0)=1):", 
                 bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC, font=FUENTE_NORMAL).pack(anchor="w")

        for i in range(n):
            f_row = tk.Frame(frame_inputs, bg=COLOR_FONDO)
            f_row.pack(fill="x", pady=2)
            tk.Label(f_row, text=f"C{i+1}: ", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side=tk.LEFT)
            entry = tk.Entry(f_row, bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white",
                             relief="flat", highlightthickness=1, highlightbackground="#555")
            entry.pack(side=tk.LEFT, fill="x", expand=True)
            sugerencia = f"y{''.join(['\'' for _ in range(i)])}(0)=0"
            entry.insert(0, sugerencia)
            self.entries_condiciones_variacion.append(entry)

    def aplicar_condiciones_variacion(self):
        # Botón específico del panel izquierdo
        lista_textos = [e.get().strip() for e in self.entries_condiciones_variacion if e.get().strip()]
        if not lista_textos:
            messagebox.showwarning("Atención", "No ingresó condiciones.")
            return

        try:
            log = self.solver.gestionar_condiciones_iniciales(lista_textos)
            self.etiqueta_resultado.insert(tk.END, "\n\n=== CONSTANTES ===\n")
            self.etiqueta_resultado.insert(tk.END, log + "\n")
            self.etiqueta_resultado.insert(tk.END, f"FINAL:\n{sp.pretty(self.solver.get_solucion_final())}\n")
            self.etiqueta_resultado.see(tk.END)
            
            # Actualizar gráfica con la nueva solución particular
            self.actualizar_grafica_manual()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_grafica_manual(self):
        """
        Lee los inputs Xmin/Xmax del panel derecho y redibuja.
        """
        if not self.ultimo_metodo_exitoso or not self.solver:
            return

        # Leer rangos
        try:
            xmin = float(self.entry_xmin.get())
            xmax = float(self.entry_xmax.get())
            if xmin >= xmax:
                messagebox.showerror("Error", "Min debe ser menor que Max")
                return
        except ValueError:
            messagebox.showerror("Error", "Rango inválido")
            return

        self.graficar_en_panel_derecho(self.ultimo_metodo_exitoso, xmin, xmax)

    def graficar_en_panel_derecho(self, metodo, xmin, xmax):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        fig = None
        msg = ""
        
        plt.style.use('dark_background')

        try:
            if metodo == "variacion":
                # Método Variation ya retorna figura
                fig, msg = self.solver.generar_grafica_tk(x_min=xmin, x_max=xmax)
            
            elif metodo == "coeficientes":
                # Construcción manual para CoefIndet
                if self.solver.sol is None: return
                expr = self.solver.sol.rhs
                x_sym = sp.Symbol('x')
                
                # Reemplazar Cs por 1 si no hay condiciones
                params = expr.free_symbols
                subs_dict = {s: 1 for s in params if str(s).startswith('C')}
                expr_num = expr.subs(subs_dict)

                f_num = sp.lambdify(x_sym, expr_num, "numpy")
                x_vals = np.linspace(float(xmin), float(xmax), 400)
                
                try:
                    y_vals = f_num(x_vals)
                    if np.isscalar(y_vals) or (isinstance(y_vals, np.ndarray) and y_vals.shape != x_vals.shape):
                        y_vals = np.full_like(x_vals, float(expr_num))
                except:
                    y_vals = np.full_like(x_vals, float(expr_num))

                fig = plt.figure(figsize=(6, 4), dpi=100)
                plt.plot(x_vals, y_vals, label="y(x)", color="#4CAF50")
                plt.title("Solución Coef. Indeterminados")
                plt.xlabel("x")
                plt.ylabel("y")
                plt.grid(True, color="#444")
                plt.legend()

            if fig:
                fig.patch.set_facecolor(COLOR_PANEL)
                self.canvas = FigureCanvasTkAgg(fig, master=self.panel_derecho)
                self.canvas.draw()
                widget = self.canvas.get_tk_widget()
                widget.pack(fill=tk.BOTH, expand=True)
            else:
                if msg: messagebox.showwarning("Gráfica", msg)

        except Exception as e:
            messagebox.showerror("Error Gráfica", f"No se pudo graficar: {e}")

if __name__ == "__main__":
    Interfaz()