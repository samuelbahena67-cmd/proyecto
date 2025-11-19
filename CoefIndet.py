# CoefIndet.py (corregido y mejorado)
from sympy import (
    symbols, Function, Eq, dsolve, sin, cos, tan, exp, log,
    simplify, nsimplify, lambdify, Derivative, sympify
)
import matplotlib.pyplot as plt
import numpy as np
import re

class CoefIndet:
    def __init__(self, ecuacion):
        self.ecuacion_raw = ecuacion.replace('^', '**').strip()
        self.ecuacion_raw = self._insert_missing_multiplication(self.ecuacion_raw)

        self.x = symbols('x')
        self.y_func = Function('y')(self.x)
        self.sol = None
        self.CI = {}
        self.C_symbols = []
        self.orden = 0
        self._parse_ecuacion()

    # -------------------------------------------------------
    # Inserta multiplicaciones faltantes: sin(3x) → sin(3*x)
    # -------------------------------------------------------
    def _insert_missing_multiplication(self, s):
        s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
        s = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', s)
        return s

    # -------------------------------------------------------
    # Reemplazos estrictos: y'', y', y
    # -------------------------------------------------------
    def _replace_derivs_strict(self, s):
        s = s.replace("y''", "Derivative(y_func, x, 2)")
        s = s.replace("y'", "Derivative(y_func, x)")
        s = re.sub(r"(?<![A-Za-z0-9_])y(?![A-Za-z0-9_])", "y_func", s)
        return s

    # -------------------------------------------------------
    # Parser completo
    # -------------------------------------------------------
    def _parse_ecuacion(self):
        if '=' not in self.ecuacion_raw:
            raise ValueError("La ecuación debe tener '=' y usar notación: y, y', y''")

        lhs, rhs = self.ecuacion_raw.split('=', 1)
        lhs_t = self._replace_derivs_strict(lhs.strip())
        rhs_t = self._replace_derivs_strict(rhs.strip())

        contexto = {
            "Derivative": Derivative,
            "y_func": self.y_func,
            "x": self.x,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "exp": exp,
            "ln": log,
            "log": log
        }

        try:
            self.lhs = sympify(lhs_t, locals=contexto)
            self.rhs = sympify(rhs_t, locals=contexto)
        except Exception as e:
            raise ValueError(f"Error al parsear la ecuación: {e}")

        # Calcular orden
        self.orden = 0
        for d in self.lhs.atoms(Derivative):
            self.orden = max(self.orden, len(d.variables))

    # -------------------------------------------------------
    # Condiciones iniciales
    # -------------------------------------------------------
    def agregar_CI(self, ci_list):
        for ci in ci_list:
            if '=' not in ci:
                raise ValueError(f"CI inválida: {ci}")

            left, right = ci.split('=', 1)
            left = left.strip()
            val = sympify(right.strip(), locals={"x": self.x})

            m0 = re.match(r"^\s*y\(\s*([^\)]+)\s*\)\s*$", left)
            m1 = re.match(r"^\s*y'\(\s*([^\)]+)\s*\)\s*$", left)
            m2 = re.match(r"^\s*y''\(\s*([^\)]+)\s*\)\s*$", left)

            if m0:
                x0 = sympify(m0.group(1))
                self.CI[self.y_func.subs({self.x: x0})] = val
            elif m1:
                x0 = sympify(m1.group(1))
                self.CI[Derivative(self.y_func, self.x).subs({self.x: x0})] = val
            elif m2:
                x0 = sympify(m2.group(1))
                self.CI[Derivative(self.y_func, self.x, 2).subs({self.x: x0})] = val
            else:
                raise ValueError(f"Formato de CI no soportado: {ci}")

    # -------------------------------------------------------
    # Resolver
    # -------------------------------------------------------
    def resolver(self):
        eq = Eq(self.lhs - self.rhs, 0)
        if self.CI:
            self.sol = dsolve(eq, self.y_func, ics=self.CI)
        else:
            self.sol = dsolve(eq, self.y_func)

    # -------------------------------------------------------
    # Mostrar solución
    # -------------------------------------------------------
    def mostrar_sol(self):
        if self.sol is None:
            return "Aún no se resuelve."

        expr = simplify(self.sol.rhs)
        self.C_symbols = sorted(
            [s for s in expr.free_symbols if str(s).startswith("C")],
            key=lambda z: str(z)
        )

        try:
            expr = nsimplify(expr)
        except:
            pass

        return str(expr)

    # -------------------------------------------------------
    # Gráfica
    # -------------------------------------------------------
    def graficar(self):
        if self.sol is None:
            print("No hay solución para graficar.")
            return

        expr = simplify(self.sol.rhs)
        subs = {C: 1 for C in self.C_symbols}
        expr_num = expr.subs(subs)

        try:
            f = lambdify(self.x, expr_num, "numpy")
            x_vals = np.linspace(-10, 10, 400)
            y_vals = f(x_vals)
        except:
            x_vals = np.linspace(-10, 10, 400)
            y_vals = [float(expr_num.subs({self.x: x})) for x in x_vals]

        plt.figure(figsize=(8, 4))
        plt.plot(x_vals, y_vals, label="y(x)")
        plt.grid(True)
        plt.legend()
        plt.show()