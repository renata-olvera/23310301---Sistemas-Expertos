import re
import sys
from pathlib import Path

from interprete import CuadernoLogico, ReglaInvalida


def dividir_texto(texto):
    return [parte.strip() for parte in re.split(r"\r?\n+|(?<=[.!?;])\s+", texto) if parte.strip()]


def main():
    archivo = Path(sys.argv[1] if len(sys.argv) > 1 else "problema.txt")
    try:
        contenido = archivo.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        print(f"No se pudo abrir el archivo: {error}")
        return 1

    cuaderno = CuadernoLogico()
    pendientes = []
    for frase in dividir_texto(contenido):
        try:
            cuaderno.anadir(frase)
        except ReglaInvalida as error:
            pendientes.append((frase, error))

    print("\nANÁLISIS DEL PROBLEMA")
    print("\nPROPOSICIONES")
    for codigo, proposicion in cuaderno.atomos.items():
        print(f"  {codigo}: {proposicion}")

    print("\nREGLAS")
    for regla in cuaderno.reglas:
        print(f"  {regla['id']}: {regla['formula']}")

    if pendientes:
        print("\nREVISAR ESTAS ORACIONES")
        for frase, motivo in pendientes:
            print(f"  {frase}\n  Motivo: {motivo}")

    print(f"\nResumen: {len(cuaderno.atomos)} átomos, {len(cuaderno.reglas)} reglas, "
          f"{len(pendientes)} pendientes.")
    return bool(pendientes)


if __name__ == "__main__":
    raise SystemExit(main())
