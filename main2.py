from CoefIndet import CoefIndet

def main():
    print("===== SOLVER DE ECUACIONES DIFERENCIALES (Coeficientes Indeterminados) =====")
    print("Ejemplos válidos:")
    print("  y'' + y = sin(x)")
    print("  y'' + y = sin(3x)")
    print("  y'' - 4*y' + 4*y = exp(x)")
    print("  y'' + 9*y = cos(3x)")
    print("  y'' + y = tan(x)")
    print("  y'' + 4*y = ln(x)")
    print("  y'' + 2*y' + y = x*exp(x)")
    print("  y'' - 9*y = 5")
    print()

    ecuacion = input("Ingresa la ecuación diferencial: ").strip()

    try:
        solver = CoefIndet(ecuacion)

        print(f"\nLa ecuación es de *orden {solver.orden}*.")
        print(f"Puedes ingresar hasta {solver.orden} condiciones iniciales.\n")

        if solver.orden > 0:
            resp = input("¿Deseas agregar condiciones iniciales? (s/n): ").strip().lower()
            if resp == "s":
                ci_list = []
                for i in range(1, solver.orden + 1):
                    ci_list.append(input(f"CI{i}: ").strip())
                solver.agregar_CI(ci_list)

        solver.resolver()

        print("\nSolución (una sola línea):")
        print(solver.mostrar_sol())

        print("\nGenerando gráfica automáticamente...")
        solver.graficar()

    except Exception as e:
        print(f"\nHa ocurrido un error: {e}")
        print("Revisa el formato de la ecuación.")

if __name__ == "__main__":
    main()