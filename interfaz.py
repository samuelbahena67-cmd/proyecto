import tkinter as tk
from tkinter import Toplevel, messagebox, simpledialog
import sympy as sp
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt

# Import de EDOSolver se hará dinámicamente según el método
# CoefIndet se importa para el método de coeficientes indeterminados
from CoefIndet import CoefIndet


class Interfaz:
    def __init__(self):
        self.solver = None
        self.valores_iniciales = {}
        self.orden_ecuacion = None  # Guardará el orden una vez resuelta la homogénea

        self.ventana = tk.Tk()
        self.ventana.title("Resolución de Ecuaciones Diferenciales de Orden Superior")
        self.ventana.geometry("700x700")

        # Imagen
        try:
            imagen_original = Image.open("ICO.jpg")
            imagen_redimensionada = imagen_original.resize((300, 200))
            imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
            etiqueta_imagen = tk.Label(self.ventana, image=imagen_tk)
            etiqueta_imagen.image = imagen_tk
            etiqueta_imagen.pack(pady=10)
        except:
            pass  # Si no hay imagen, no hay problema

        # Mensaje de alerta al inicio
        self.ventana.after(500, lambda: messagebox.showwarning(
            "Información",
            "Recuerde: los valores iniciales solo se pueden ingresar después de resolver la ecuación."
        ))

        # Entrada de ecuación
        tk.Label(self.ventana, text="Ingrese la ecuación diferencial:", font=("Arial", 12)).pack(pady=5)
        self.entrada_ecuacion = tk.Entry(self.ventana, width=50)
        self.entrada_ecuacion.pack()

        # Botones
        tk.Button(self.ventana, text="Insertar valores iniciales (opcional)",
                  command=self.abrir_valores_iniciales).pack(pady=5)
        tk.Button(self.ventana, text="Resolver",
                  command=self.resolver_ecuacion, bg="#4CAF50", fg="white").pack(pady=10)

        # Selector de método
        self.metodo = tk.StringVar(value="variacion")
        tk.Label(self.ventana, text="Seleccione el método:", font=("Arial", 12)).pack()
        tk.Radiobutton(self.ventana, text="Variación de Parámetros",
                       variable=self.metodo, value="variacion").pack()
        tk.Radiobutton(self.ventana, text="Coeficientes Indeterminados",
                       variable=self.metodo, value="indeterminados").pack()

        # Panel de resultados (Texto para mostrar pasos)
        self.etiqueta_resultado = tk.Text(self.ventana, font=("Arial", 10), fg="blue", width=80, height=25)
        self.etiqueta_resultado.pack(pady=10)
        self.etiqueta_resultado.config(state=tk.NORMAL)

        self.ventana.mainloop()

    def abrir_valores_iniciales(self):
        if not self.solver or self.orden_ecuacion is None:
            messagebox.showerror(
                "Error",
                "Primero debe resolver la ecuación para determinar el orden y luego podrá ingresar valores iniciales."
            )
            return

        ventana_vi = Toplevel(self.ventana)
        ventana_vi.title("Valores Iniciales")
        ventana_vi.geometry("300x" + str(self.orden_ecuacion * 60 + 80) + "+200+200")

        tk.Label(ventana_vi, text=f"Ingrese {self.orden_ecuacion} valores iniciales (opcional):", font=("Arial", 12)).pack(pady=10)

        entradas = []
        for i in range(self.orden_ecuacion):
            tk.Label(ventana_vi, text=f"y^{i}(0) = ").pack()
            entrada = tk.Entry(ventana_vi)
            entrada.pack()
            entradas.append(entrada)

        def guardar():
            try:
                self.valores_iniciales.clear()
                for i, entrada in enumerate(entradas):
                    valor_texto = entrada.get().strip()
                    if valor_texto != "":
                        valor = float(valor_texto)
                        self.valores_iniciales[f'cond_{i}'] = valor
                messagebox.showinfo("Valores guardados", f"Se guardaron {len(self.valores_iniciales)} condiciones iniciales.")
                ventana_vi.destroy()
            except ValueError:
                messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos")

        tk.Button(ventana_vi, text="Guardar valores", command=guardar).pack(pady=10)

    def resolver_ecuacion(self):
        ecuacion = self.entrada_ecuacion.get().strip()
        if not ecuacion:
            messagebox.showerror("Error", "Por favor ingrese una ecuación diferencial.")
            return

        try:
            # Crear solver según método seleccionado
            if self.metodo.get() == "variacion":
                from MetodoVariacionParametros import EDOSolver
                self.solver = EDOSolver(ecuacion)
            else:
                self.solver = CoefIndet(ecuacion)

            self.etiqueta_resultado.delete("1.0", tk.END)

            # --------- Variación de parámetros ----------
            if self.metodo.get() == "variacion":
                self.etiqueta_resultado.insert(tk.END, "PASO 1: Resolver homogénea\n")
                self.solver.resolver_homogenea()
                self.etiqueta_resultado.insert(tk.END, "\nRaíces:\n" + sp.pretty(self.solver.raices) + "\n")
                self.etiqueta_resultado.insert(tk.END, "\nCFS:\n" + sp.pretty(self.solver.CFS) + "\n")
                self.etiqueta_resultado.insert(tk.END, "\nSolución Homogénea (y_h):\n" + sp.pretty(self.solver.solucionHomogenea) + "\n")

                self.orden_ecuacion = len(self.solver.CFS)

                self.etiqueta_resultado.insert(tk.END, "\nPASO 2: Resolver particular\n")
                self.solver.resolver_particular()
                self.etiqueta_resultado.insert(tk.END, "\nIntegrales (u_k):\n" + sp.pretty(self.solver.matriz_U_integrada) + "\n")
                self.etiqueta_resultado.insert(tk.END, "\nSolución Particular (y_p):\n" + sp.pretty(self.solver.y_p) + "\n")

                self.etiqueta_resultado.insert(tk.END, "\nPASO 3: Solución General\n")
                self.solver.crear_solucion_general()
                self.etiqueta_resultado.insert(tk.END, "\nSolución General (y_g = y_h + y_p):\n" + sp.pretty(self.solver.get_solucion_general()) + "\n")

                # Aplicar condiciones iniciales
                if self.valores_iniciales:
                    self.solver.gestionar_condiciones_iniciales(self.valores_iniciales)
                    self.etiqueta_resultado.insert(tk.END, "\nSolución Final (con condiciones iniciales):\n" +
                                                   sp.pretty(self.solver.get_solucion_final()) + "\n")
                else:
                    self.etiqueta_resultado.insert(tk.END, "\nNo se aplicaron condiciones iniciales.\n")

            # --------- Coeficientes indeterminados ----------
            else:
                self.etiqueta_resultado.insert(tk.END, "Resolviendo por Coeficientes Indeterminados...\n")
                self.solver.resolver()
                self.orden_ecuacion = self.solver.orden

                if self.valores_iniciales:
                    ci_list = []
                    for i, v in self.valores_iniciales.items():
                        # Construir string compatible con CoefIndet
                        # Asumimos que las condiciones son en x=0 y derivadas consecutivas
                        ci_str = f"y({0})={v}"
                        ci_list.append(ci_str)
                    self.solver.agregar_CI(ci_list)
                    self.solver.resolver()  # Resolver nuevamente con CI

                self.etiqueta_resultado.insert(tk.END, "\nSolución:\n" + self.solver.mostrar_sol() + "\n")

            # Preguntar si desea graficar
            self.etiqueta_resultado.insert(tk.END, "\n¿Desea graficar la solución final? (s/n): ")

            def procesar_respuesta(event):
                contenido = self.etiqueta_resultado.get("1.0", tk.END).strip().split("\n")
                ultima_linea = contenido[-1].strip().lower()

                if ultima_linea == 's':
                    self.etiqueta_resultado.insert(tk.END, "\nHa seleccionado 's'. Se abrirá ventana para rango.\n")
                    self.etiqueta_resultado.unbind("<Return>")
                    self.preguntar_rango_grafica()
                elif ultima_linea == 'n':
                    self.etiqueta_resultado.insert(tk.END, "\nNo se generará la gráfica.\n")
                    self.etiqueta_resultado.unbind("<Return>")
                else:
                    self.etiqueta_resultado.insert(tk.END, "\nEntrada no válida. Ingrese 's' o 'n'.\n")

            self.etiqueta_resultado.bind("<Return>", procesar_respuesta)

        except Exception as e:
            messagebox.showerror("Error al resolver", str(e))

    def preguntar_rango_grafica(self):
        try:
            x_min_in = simpledialog.askfloat("Rango de x", "Ingrese el valor mínimo de x para graficar (ej: -10):")
            x_max_in = simpledialog.askfloat("Rango de x", "Ingrese el valor máximo de x para graficar (ej: 10):")

            if x_min_in is None or x_max_in is None:
                self.etiqueta_resultado.insert(tk.END, "Rango no proporcionado. No se graficará.\n")
                return

            if x_min_in >= x_max_in:
                self.etiqueta_resultado.insert(tk.END, "Error: x_min debe ser menor que x_max. No se graficará.\n")
                return

            plt.clf()
            plt.close('all')

            if self.metodo.get() == "variacion":
                self.solver.graficar_solucion_final(x_min_in, x_max_in, "solucion_edo.png")
            else:
                self.solver.graficar()

            if os.path.exists("solucion_edo.png"):
                os.startfile("solucion_edo.png")
                self.etiqueta_resultado.insert(tk.END, "Gráfica generada y abierta automáticamente.\n")
            else:
                self.etiqueta_resultado.insert(tk.END, "Gráfica generada.\n")

        except Exception as e:
            self.etiqueta_resultado.insert(tk.END, f"Error al graficar: {e}\n")


if __name__ == "__main__":
    Interfaz()