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

    def gestionar_condiciones_iniciales(self, lista_condiciones_str):
        if self.y_general == 0:
            return "Error: Debe llamar a .crear_solucion_general() antes."

        patron = re.compile(r"^\s*y('*)\s*\(\s*([-\d\.]+)\s*\)\s*=\s*([-\d\.]+)\s*$")

        datos_procesados = []
        
        for cadena in lista_condiciones_str:
            match = patron.match(cadena)
            if match:
                try:
                    comillas = match.group(1)
                    orden_k = len(comillas)
                    
                    valor_x = float(match.group(2))
                    valor_y = float(match.group(3))
                    
                    datos_procesados.append((orden_k, valor_x, valor_y))
                except ValueError:
                    return f"Error al leer números en: {cadena}"
            else:
                return f"Formato inválido en: '{cadena}'. Use formato y''(0)=1"

        if len(datos_procesados) != self.grado:
            return f"Error: Se requieren {self.grado} condiciones, se recibieron {len(datos_procesados)}."

        ecuaciones = []
        log_texto = "Sistema generado:\n"
        
        try:
            for k, x0, y0 in datos_procesados:
                if k == 0:
                    derivada_k = self.y_general
                else:
                    derivada_k = sp.diff(self.y_general, self.x, k)
                
                eq_sustituida = derivada_k.subs(self.x, x0).doit()
                ecuacion_final = sp.Eq(eq_sustituida, y0)
                ecuaciones.append(ecuacion_final)
                log_texto += f"  y{''.join(['\'' for _ in range(k)])}({x0}) = {y0}\n"

            soluciones_C = sp.solve(ecuaciones, self.C, dict=True)
            
            if soluciones_C:
                valores_C = soluciones_C[0]
                self.y_final_sustituida = self.y_general.subs(valores_C).doit()
                log_texto += "\nConstantes:\n" + sp.pretty(valores_C)
                return log_texto
            else:
                return "No se encontró solución única para las constantes."
                
        except Exception as e:
            return f"Error matemático al resolver condiciones: {e}"

    def generar_grafica_tk(self, x_min=-10, x_max=10):
        if self.y_final_sustituida == 0:
            return None, "Error: No hay solución final para graficar."
        
        if any(c in self.y_final_sustituida.free_symbols for c in self.C):
            return None, "La solución aún contiene constantes C sin resolver."

        print(f"\nGenerando gráfico de la solución final de x={x_min} a x={x_max}...")
        
        try:
            f_numerica = sp.lambdify(self.x, self.y_final_sustituida, 'numpy')
            x_vals = np.linspace(float(x_min), float(x_max), 400)
            
            try:
                y_vals = f_numerica(x_vals)
                if np.isscalar(y_vals) or (isinstance(y_vals, np.ndarray) and y_vals.shape != x_vals.shape):
                     y_vals = np.full_like(x_vals, float(self.y_final_sustituida))
            except:
                 y_vals = np.full_like(x_vals, float(self.y_final_sustituida))
            
            fig = plt.figure(figsize=(6, 4), dpi=100)
            plt.plot(x_vals, y_vals, label='y(x)')
            plt.xlabel("x")
            plt.ylabel("y(x)")
            plt.title("Solución Final de la Ecuación Diferencial")
            plt.grid(True)
            plt.legend()
            
            return fig, "Gráfico generado con éxito"
            
        except Exception as e:
            print(f"\nError al generar el gráfico: {e}")
            return None, str(e)

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