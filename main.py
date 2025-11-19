from MetodoVariacionParametros import EDOSolver

import sympy as sp

if __name__ == "__main__":
    
    # 1. Entrada de datos
    f = input("Ingresa Ecuacion diferencial (ej: y'' + y = x)\n")
    
    try:
        solver = EDOSolver(f)

        print("\nPASO 1")
        solver.resolver_homogenea()
        
        print("\nRaíces:")
        sp.pprint(solver.raices)
        print("\nCFS:")
        sp.pprint(solver.CFS)
        print("\nSolución Homogénea (y_h):")
        sp.pprint(solver.solucionHomogenea)

        print("\nPASO 2")
        solver.resolver_particular()
        
        print("\nIntegrales (u_k):")
        sp.pprint(solver.matriz_U_integrada)
        print("\nSolución Particular (y_p):")
        sp.pprint(solver.y_p)

        print("\nPASO 3")
        solver.crear_solucion_general()
        
        print("\nSolución General (y_g = y_h + y_p):")
        sp.pprint(solver.get_solucion_general())

        solver.gestionar_condiciones_iniciales()

        #creacion de grafica

        while True:
            decision = input("\n¿Desea graficar la solución final? (s/n): ").strip().lower()
            if decision in ['s', 'n']:
                break
        
        if decision == 's':
            try:
                x_min_in = float(input("  Ingrese el valor mínimo de x para graficar (ej: -10): "))
                x_max_in = float(input("  Ingrese el valor máximo de x para graficar (ej: 10): "))
                
                if x_min_in >= x_max_in:
                    print("Error: x_min debe ser menor que x_max.")
                else:
                    solver.graficar_solucion_final(x_min_in, x_max_in, "solucion_edo.png")
            except ValueError:
                print("Entrada no válida. Se omitirá el gráfico.")
        
        print("\nRESULTADOS FINALES ")
        
        print("\nSolución General (con C):")
        sp.pprint(solver.get_solucion_general())
        
        print("\nSolución Final (con C resueltas si se dieron):")
        sp.pprint(solver.get_solucion_final())

    except Exception as e:
        print(f"\nHa ocurrido un error en la ejecución: {e}")
        print("Por favor, revise el formato de la ecuación.")