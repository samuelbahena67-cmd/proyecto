# ============================================================
#  SOLVER DE ECUACIONES DIFERENCIALES (Coeficientes Indeterminados)
#  Versión 1: Mejorada
# ============================================================

from sympy import (
    symbols, Function, Eq, dsolve, sin, cos, tan, exp, log,
    simplify, nsimplify, lambdify, Derivative, sympify
)
import matplotlib.pyplot as plt
import numpy as np
import re


class CoefIndet:
    def __init__(self, ecuacion):
        # Normalizar ^ -> **
        self.ecuacion_raw = ecuacion.replace('^', '**').strip()
        # Insertar multiplicaciones faltantes (2x -> 2*x)
        self.ecuacion_raw = self._insert_missing_multiplication(self.ecuacion_raw)

        self.x = symbols('x')
        self.y_func = Function('y')(self.x)
        self.sol = None
        self.CI = {}
        self.C_symbols = []
        self.orden = 0

        self._parse_ecuacion()

    # ---------------------------------------------------------
    def _insert_missing_multiplication(self, s):
        s = re.sub(r'(\d)\s*([a-zA-Z(])', r'\1*\2', s)
        s = re.sub(r'([a-zA-Z)])\s*(\d)', r'\1*\2', s)
        return s

    # ---------------------------------------------------------
    def _replace_derivs(self, s):
        pattern_n = r"y\(\s*(\d+)\s*\)"
        s = re.sub(pattern_n, lambda m: f"Derivative(y_func, x, {m.group(1)})", s)

        pattern_ticks = r"y('{1,})"
        def repl_ticks(m):
            n = len(m.group(1))
            return f"Derivative(y_func, x, {n})"
        s = re.sub(pattern_ticks, repl_ticks, s)

        s = re.sub(r"(?<![A-Za-z0-9_])y(?![A-Za-z0-9_\(])", "y_func", s)
        return s

    # ---------------------------------------------------------
    def _parse_ecuacion(self):
        if '=' not in self.ecuacion_raw:
            raise ValueError("La ecuación debe contener '='.")

        lhs, rhs = self.ecuacion_raw.split('=', 1)
        lhs_t = self._replace_derivs(lhs.strip())
        rhs_t = self._replace_derivs(rhs.strip())

        contexto = {
            "Derivative": Derivative,
            "y_func": self.y_func,
            "x": self.x,
            "sin": sin, "cos": cos, "tan": tan,
            "exp": exp, "ln": log, "log": log
        }

        try:
            self.lhs = sympify(lhs_t, locals=contexto)
            self.rhs = sympify(rhs_t, locals=contexto)
        except Exception as e:
            raise ValueError(f"Error al parsear la ecuación: {e}")

        self.orden = 0
        for d in self.lhs.atoms(Derivative):
            try:
                order = len(d.variables)
            except Exception:
                order = 1
            if order > self.orden:
                self.orden = order

    # ---------------------------------------------------------
    def agregar_CI(self, ci_list):
        for ci in ci_list:
            if '=' not in ci:
                raise ValueError(f"CI inválida: {ci}")

            left, right = ci.split('=', 1)
            left = left.strip()
            val = sympify(right.strip(), locals={"x": self.x})

            m_general = re.match(r"^\s*y\(\s*(\d+)\s*\)\s*\(\s*([^\)]+)\s*\)\s*$", left)
            if m_general:
                n = int(m_general.group(1))
                x0 = sympify(m_general.group(2))
                self.CI[Derivative(self.y_func, self.x, n).subs({self.x: x0})] = val
                continue

            m0 = re.match(r"^\s*y\(\s*([^\)]+)\s*\)\s*$", left)
            if m0:
                x0 = sympify(m0.group(1))
                self.CI[self.y_func.subs({self.x: x0})] = val
                continue

            m1 = re.match(r"^\s*y'\(\s*([^\)]+)\s*\)\s*$", left)
            if m1:
                x0 = sympify(m1.group(1))
                self.CI[Derivative(self.y_func, self.x).subs({self.x: x0})] = val
                continue

            m2 = re.match(r"^\s*y''\(\s*([^\)]+)\s*\)\s*$", left)
            if m2:
                x0 = sympify(m2.group(1))
                self.CI[Derivative(self.y_func, self.x, 2).subs({self.x: x0})] = val
                continue

            m_short = re.match(r"^\s*y\(\s*(\d+)\s*\)\s*$", left)
            if m_short:
                n = int(m_short.group(1))
                self.CI[Derivative(self.y_func, self.x, n).subs({self.x: 0})] = val
                continue

            raise ValueError(f"Formato de CI no soportado: {ci}")

    def resolver(self):
        eq = Eq(self.lhs - self.rhs, 0)
        
        if self.CI:
            print(f"Resolviendo con condiciones: {self.CI}") 
            try:
                self.sol = dsolve(eq, ics=self.CI)
            except Exception as e:
                print(f"Error aplicando CI en dsolve: {e}")

                self.sol = dsolve(eq)
        else:
            self.sol = dsolve(eq)

    def mostrar_sol(self):
        if self.sol is None:
            return "Primero debes resolver la ecuación."

        expr = simplify(self.sol.rhs)
        self.C_symbols = sorted([s for s in expr.free_symbols if str(s).startswith("C")], key=lambda z: str(z))
        try:
            expr = nsimplify(expr)
        except Exception:
            pass
        return str(expr)

    # ---------------------------------------------------------
    def graficar(self):
        if self.sol is None:
            print("No hay solución para graficar.")
            return

        expr = simplify(self.sol.rhs)
        for C in [s for s in expr.free_symbols if 'C' in str(s)]:
            expr = expr.subs(C, 1)

        f = lambdify(self.x, expr, "numpy")
        x_vals = np.linspace(-10, 10, 400)
        try:
            y_vals = f(x_vals)
        except Exception:
            y_vals = [float(expr.subs({self.x: x})) for x in x_vals]

        plt.plot(x_vals, y_vals)
        plt.grid()
        plt.title("Solución aproximada (C=1)")
        plt.xlabel("x")
        plt.ylabel("y(x)")
        plt.show()