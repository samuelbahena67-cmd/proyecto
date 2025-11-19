import numpy as np
import sympy as sp
from sympy import degree, roots, E, solve
import matplotlib.pyplot as plt
import re

from sympy.parsing.sympy_parser import (
    parse_expr, 
    standard_transformations, 
    implicit_multiplication_application, 
    convert_xor
)

class EDOSolver:
    
    def __init__(self, ecuacion_str: str):
        self.x = sp.Symbol('x')
        self.y = sp.Symbol('y')
        
        self.ecuacion_str = ecuacion_str
        self.fHomogenea = None
        self.fComplementaria = None
        
        self.grado = 0
        self.raices = {}
        self.CFS = []
        self.C = []
        self.U = []
        
        self.solucionHomogenea = 0
        self.solucionParticular_u = 0
        self.matriz_U_integrada = None
        self.y_p = 0
        self.y_general = 0
        self.y_final_sustituida = 0
        
        try:
            self._parsear_ecuacion()
            print(f"Ecuación parseada. Orden (grado) detectado: {self.grado}")
        except Exception as e:
            print(f"Error fatal al parsear la ecuación: {e}")
            raise



    def resolver_homogenea(self):
        #Buscar raices funcion
        self.raices = roots(self.fHomogenea, self.y)
        
        #CFS

        self.CFS = self._revisarMultiplicidad(self.raices)

        self.C = sp.symbols(f'c1:{self.grado+1}')
        self.U = sp.symbols(f'u1:{self.grado+1}')

        #Solucion Homogenea con CFS (c1, c2, ..., cn)
        self.solucionHomogenea = 0
        #Solucion no homogenea (u1, u2, ..., un)
        self.solucionParticular_u = 0

        for i in range(self.grado):
            self.solucionHomogenea += self.C[i] * self.CFS[i]
            self.solucionParticular_u += self.U[i] * self.CFS[i]
        
    def resolver_particular(self):
        wronskiano_matriz = self._hacerWronskiano()
        soluciones_determinantes = self._hacerDeterminantesComplementaria(wronskiano_matriz)
        self.matriz_U_integrada = self._integrarObtenerU(soluciones_determinantes)
        self.y_p = self._sustitucionU()

    #Solucion General
    def crear_solucion_general(self):
        solucionGeneral = self.solucionHomogenea + self.y_p

        solucionGeneral = solucionGeneral.doit()
        solucionGeneral = solucionGeneral.subs(sp.E, sp.exp(1))
        #solucionGeneral = sp.exptrigsimp(solucionGeneral)
        #solucionGeneral = sp.simplify(solucionGeneral)
        solucionGeneral = sp.expand(solucionGeneral)
        self.y_general = solucionGeneral
        self.y_final_sustituida = self.y_general

    def gestionar_condiciones_iniciales(self):
        if self.y_general == 0:
            print("Error: Debe llamar a .crear_solucion_general() antes.")
            return

        print(f"\n--- 4. Condiciones Iniciales ---")
        
        lista_condiciones = []
        while True:
            decision = input("¿Desea ingresar condiciones iniciales? (s/n): ").strip().lower()
            if decision in ['s', 'n']:
                break
            print("Respuesta no válida. Por favor, ingrese 's' o 'n'.")

        if decision == 'n':
            print("No se ingresaron condiciones. La Solución General es la final.")
            self.y_final_sustituida = self.y_general
            return

        print(f"Debe ingresar {self.grado} condiciones.")
        print("Use el formato: y(x0)=y0, y'(x0)=y0, y''(x0)=y0, etc.")
        patron_condicion = re.compile(r"^\s*y('*?)\s*\(\s*(-?[\d\.]+)\s*\)\s*=\s*(-?[\d\.]+)\s*$")

        for i in range(self.grado):
            while True:
                entrada = input(f"  Ingrese la condición {i+1} de {self.grado}: ").strip()
                match = patron_condicion.match(entrada)
                if match:
                    try:
                        orden_k = len(match.group(1))
                        valor_x = float(match.group(2))
                        valor_y = float(match.group(3))
                        lista_condiciones.append((orden_k, valor_x, valor_y))
                        print(f"    -> Detectado: orden={orden_k}, x0={valor_x}, y0={valor_y}")
                        break
                    except ValueError:
                        print("  Error al convertir los números. Intente de nuevo.")
                else:
                    print("  Formato no válido. Intente de nuevo.")
        
        if len(lista_condiciones) != self.grado:
            print(f"Error: Se esperaban {self.grado} condiciones, pero se ingresaron {len(lista_condiciones)}.")
            print("No se calcularán las constantes.")
            return

        ecuaciones = []
        print("\nConstruyendo sistema de ecuaciones para las constantes:")
        
        for k, x0, y0 in lista_condiciones:
            print(f"  Procesando condición: y{''*k}({x0}) = {y0}")
            if k == 0:
                derivada_k = self.y_general
            else:
                derivada_k = sp.diff(self.y_general, self.x, k)
            
            eq_sustituida = derivada_k.subs(self.x, x0)
            eq_sustituida = eq_sustituida.doit()
            ecuacion_final = sp.Eq(eq_sustituida, y0)
            ecuaciones.append(ecuacion_final)
            print("    Ecuación resultante:")
            sp.pprint(ecuacion_final)

        print("\nResolviendo el sistema...")

        # ----------- CORRECCIÓN APLICADA AQUÍ -----------
        try:
            soluciones_C = sp.solve(ecuaciones, self.C, dict=True)  # Forzar diccionario
            if soluciones_C:
                # Tomar la primera solución encontrada
                valores_C = soluciones_C[0]
                self.y_final_sustituida = self.y_general.subs(valores_C).doit()
                print("\nConstantes encontradas:")
                sp.pprint(valores_C)
                print("\n--- Solución Final (con condiciones aplicadas) ---")
                sp.pprint(self.y_final_sustituida)
            else:
                print("\nNo se pudo encontrar una solución única para las constantes.")
        except Exception as e:
            print(f"\nError resolviendo el sistema de ecuaciones: {e}")
        # -----------------------------------------------

    def graficar_solucion_final(self, x_min=-10, x_max=10, filename="solucion_edo.png"):
        if self.y_final_sustituida == 0:
            print("Error: No hay solución final para graficar. Ejecute .crear_solucion_general() primero.")
            return None
        
        if any(c in self.y_final_sustituida.free_symbols for c in self.C):
            print("\nAdvertencia: La solución general aún contiene constantes (C1, C2...).")
            print("No se puede graficar. Debe ingresar condiciones iniciales primero.")
            return None

        print(f"\nGenerando gráfico de la solución final de x={x_min} a x={x_max}...")
        
        try:
            f_numerica = sp.lambdify(self.x, self.y_final_sustituida, 'numpy')
            x_vals = np.linspace(float(x_min), float(x_max), 400)
            y_vals = f_numerica(x_vals)
            
            plt.plot(x_vals, y_vals, label=f'y(x)')
            plt.xlabel("x")
            plt.ylabel("y(x)")
            plt.title("Solución Final de la Ecuación Diferencial")
            plt.grid(True)
            plt.legend()
            plt.savefig(filename)
            
            print(f"Gráfico guardado exitosamente como '{filename}'")
            return filename
            
        except Exception as e:
            print(f"\nError al generar el gráfico: {e}")
            print("La expresión puede ser demasiado compleja o no numérica.")
            return None

    def get_solucion_general(self):
        return self.y_general
    
    def get_solucion_final(self):
        return self.y_final_sustituida
    
    def get_pretty_solucion_general(self) -> str:
        return sp.pretty(self.y_general) if self.y_general != 0 else "No calculada."
    
    def get_pretty_solucion_final(self) -> str:
        return sp.pretty(self.y_final_sustituida) if self.y_final_sustituida != 0 else "No calculada."


    #Ingreso ecuacion diferencial y division en partes
    def _parsear_ecuacion(self):
        fSplit = self.ecuacion_str.split('=') 
        if len(fSplit) != 2:
            raise ValueError("La ecuación debe tener un formato 'LHS = RHS'")
        
        self.fHomogenea = self._convertirACaracteristica(fSplit[0])
        self.fComplementaria = self._convertirASimbolica(fSplit[1])
        self.grado = self._obtener_exponente_maximo(self.fHomogenea)

    #Transformar a expresion caracteristica
    def _convertirACaracteristica(self, expresionDiferencial):
        def replacer(match):
            comillas = match.group(1)
            orden = len(comillas)
            return f"y**{orden}"
        
        patron = r"y('*)"
        ecCaracteristica_str = re.sub(patron, replacer, expresionDiferencial)
        
        try:
            transformations = (standard_transformations + (implicit_multiplication_application, convert_xor))
            fCaracteristica = parse_expr(ecCaracteristica_str, 
                                         local_dict={'y': self.y}, 
                                         transformations=transformations)
            return fCaracteristica
        except Exception as e:
            print(f"Error al analizar la ecuación característica: {e}")
            raise

    #Tranformacion a expresion simbolica con x
    def _convertirASimbolica(self, expresion):
        try:
            transformations = (standard_transformations + (implicit_multiplication_application, convert_xor))

            f_locals = {
                'x': self.x,
                'e': sp.exp(1) 
            }

            funcion_simbolica = parse_expr(expresion, 
                                           local_dict=f_locals, 
                                           transformations=transformations)
            return funcion_simbolica
        except Exception as e:
            print(f"Error al analizar la función complementaria: {e}")
            raise

    #Orden mayor
    def _obtener_exponente_maximo(self, expresion):
        return int(degree(expresion, gen=self.y))
        
    #Revisar multiplicidad
    def _revisarMultiplicidad(self, raicesMultiplicidad):
        solucionesSinMultiplicidad = []
        raicesProcesadas = set()

        for raiz, multiplicidad in raicesMultiplicidad.items():
            if raiz in raicesProcesadas:
                continue
            alfa = sp.re(raiz)
            beta = sp.im(raiz)

            if beta != 0:
                raicesProcesadas.add(raiz)
                raicesProcesadas.add(sp.conjugate(raiz))
                beta = abs(beta)
                for i in range(multiplicidad):
                    s1 = (self.x**i) * sp.exp(alfa * self.x) * sp.cos(beta * self.x)
                    s2 = (self.x**i) * sp.exp(alfa * self.x) * sp.sin(beta * self.x)
                    solucionesSinMultiplicidad.extend([s1, s2])
            else:
                raicesProcesadas.add(raiz)
                for i in range(multiplicidad):
                    solucion = (self.x**i) * sp.exp(alfa * self.x)
                    solucionesSinMultiplicidad.append(solucion)

        return solucionesSinMultiplicidad

    #Matriz Wronskiano
    def _hacerWronskiano(self):
        matriz = sp.zeros(self.grado, self.grado)
        #Primer nivel de Wronskiano
        for i in range(self.grado):
            matriz[0, i] = self.CFS[i]
        #Niveles de derivadas
        for i in range(self.grado):
            for j in range(1, self.grado):
                matriz[j, i] = sp.diff(matriz[j-1, i], self.x)
        return matriz

    #Hacer determinantes
    def _hacerDeterminantesComplementaria(self, wronskiano_matriz):
        matrizCramer = sp.zeros(self.grado, 1)
        matrizCramer[self.grado-1, 0] = self.fComplementaria
        
        soluciones = wronskiano_matriz.solve(matrizCramer) 
        return soluciones

    #Integrar para obtener U1, U2, ..., Un
    def _integrarObtenerU(self, matrizSoluciones):
        matrizU = sp.zeros(self.grado, 1)
        for i in range(self.grado):
            integralSinLimpiar = matrizSoluciones[i, 0]
            integralLimpia = integralSinLimpiar.subs(sp.E, sp.exp(1))
            integralLimpia = sp.integrate(integralLimpia, self.x)
            integralLimpia = integralLimpia.doit()
            #integralLimpia = sp.exptrigsimp(integralLimpia)
            integralLimpia = sp.simplify(integralLimpia)
            #integralLimpia = sp.expand(integralLimpia)
            matrizU[i, 0] = integralLimpia
        return matrizU

    #Sustituir en U
    def _sustitucionU(self):
        soluciones = list(zip(self.U, self.matriz_U_integrada))
        solucionParticularEvaluada = self.solucionParticular_u.subs(soluciones)
        return solucionParticularEvaluada