import re
from dataclasses import dataclass


class ReglaInvalida(ValueError):
    pass


@dataclass(frozen=True)
class Expresion:
    tipo: str
    hijos: tuple = ()
    frase: str = ""


ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
PRONOMBRES = {"yo", "tú", "tu", "él", "ella", "nosotros", "nosotras", "ustedes", "ellos", "ellas"}
VERBOS = set("""
acredita acreditan activa activan anda andan aprueba aprueban apruebe apruebes
asiste asisten baila bailan canta cantan compra compran come comen corre corren
cumple cumplen detecta detectan detiene detienen duerme duermen enciende
encienden entrega entregan estudia estudian falla fallan funciona funcionan
gana ganan gira giran inicia inician juega juegan lee leen llueve paga pagan
pasa pasan pierde pierden puede pueden recibe reciben sale salen trabaja
trabajan tiene tienen termina terminan vive viven es son está están estaba
estaban hay toma toman revisa revisan entra entran manda mandan envía envían
""".split())
CONSTRUCCIONES_PENDIENTES = re.compile(
    r"\b(?:pero|porque|aunque|mientras|cuando|ni|a menos que|siempre que|"
    r"si y solo si|solo si|solamente si)\b", re.I
)


def limpiar(frase):
    return re.sub(r"\s+", " ", frase.strip()).rstrip(".!? ").strip()


def envoltura(frase):
    """Quita solo los paréntesis que encierran toda la expresión."""
    frase = frase.strip()
    while frase.startswith("(") and frase.endswith(")"):
        fondo = 0
        fin = None
        for posicion, caracter in enumerate(frase):
            fondo += (caracter == "(") - (caracter == ")")
            if fondo == 0:
                fin = posicion
                break
        if fin != len(frase) - 1:
            break
        frase = frase[1:-1].strip()
    return frase


def divisores(frase, patron):
    """Localiza conectores ignorando el contenido de paréntesis."""
    piso = 0
    indices = []
    for caracter in frase:
        indices.append(piso)
        piso += (caracter == "(") - (caracter == ")")
        if piso < 0:
            raise ReglaInvalida("Paréntesis de cierre sin apertura.")
    if piso:
        raise ReglaInvalida("Falta cerrar un paréntesis.")
    return [x for x in re.finditer(patron, frase, re.I) if indices[x.start()] == 0]


def nombre_sujeto(frase):
    partes = envoltura(frase).split()
    if not partes:
        return None
    cabeza = partes[0]
    if len(partes) > 1 and cabeza.casefold() in ARTICULOS:
        return " ".join(partes[:2])
    if cabeza.casefold() in {"si", "no"}:
        return None
    if re.fullmatch(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", cabeza):
        return cabeza
    if len(partes) > 1 and partes[1].casefold() in VERBOS:
        return cabeza
    return None


def posible_afirmacion(frase):
    frase = envoltura(frase)
    if re.fullmatch(r"[A-Z]|X\d+", frase):
        return True
    palabras = re.findall(r"[a-záéíóúüñ]+", frase.casefold())
    if palabras and palabras[0] in {"no", "se"}:
        palabras = palabras[1:]
    if not palabras:
        return False
    if palabras[0] in VERBOS:
        return True
    if len(palabras) > 1 and palabras[1] in VERBOS:
        return True
    if len(palabras) > 2 and palabras[1] == "no" and palabras[2] in VERBOS:
        return True
    if len(palabras) > 2 and palabras[0] in ARTICULOS:
        return palabras[2] in VERBOS or (
            len(palabras) > 3 and palabras[2] in {"se", "no"} and palabras[3] in VERBOS
        )
    return False


def recuperar_sujeto(frase, compartido):
    if not compartido or nombre_sujeto(frase):
        return frase
    if frase.split()[0].casefold() in PRONOMBRES:
        return frase
    return f"{compartido} {frase}"


def leer_expresion(frase, sujeto=None):
    frase = envoltura(frase)
    if not frase:
        raise ReglaInvalida("Hay una proposición vacía.")

    if re.match(r"^si\s+", frase, re.I):
        contenido = re.sub(r"^si\s+", "", frase, count=1, flags=re.I)
        cortes = divisores(contenido, r"\bentonces\b")
        if len(cortes) != 1:
            raise ReglaInvalida('Las condiciones deben usar "Si ..., entonces ...".')
        separador = cortes[0]
        antes = contenido[:separador.start()].strip(" ,")
        despues = contenido[separador.end():].strip()
        compartido = nombre_sujeto(antes) or sujeto
        return Expresion("→", (leer_expresion(antes, compartido), leer_expresion(despues, compartido)))

    negacion = re.fullmatch(r"no es cierto que\s+(.+)", frase, re.I)
    if negacion:
        return Expresion("¬", (leer_expresion(negacion.group(1), sujeto),))

    enlaces = divisores(frase, r"\b(y|o)\b")
    if enlaces:
        operadores = {enlace.group().casefold() for enlace in enlaces}
        if len(operadores) != 1:
            raise ReglaInvalida('Hay "y" y "o" juntos. Utiliza paréntesis para agrupar.')
        trozos = []
        desde = 0
        for enlace in enlaces:
            trozos.append(frase[desde:enlace.start()].strip())
            desde = enlace.end()
        trozos.append(frase[desde:].strip())
        if any(not trozo for trozo in trozos):
            raise ReglaInvalida("Falta una proposición junto al conector.")
        for trozo in trozos:
            if not trozo.startswith("(") and not posible_afirmacion(trozo):
                raise ReglaInvalida(
                    f'No está claro si "{trozo}" es una proposición completa. Reformula la oración.'
                )
        compartido = nombre_sujeto(trozos[0]) or sujeto
        operador = "∧" if "y" in operadores else "∨"
        return Expresion(operador, tuple(leer_expresion(t, compartido) for t in trozos))

    if CONSTRUCCIONES_PENDIENTES.search(frase):
        raise ReglaInvalida("Contiene una construcción gramatical no admitida.")
    if re.search(r"\b(?:si|entonces)\b", frase, re.I):
        raise ReglaInvalida('La condición debe escribirse como "Si ..., entonces ...".')

    negacion_interna = re.fullmatch(
        r"((?:(?:el|la|los|las|un|una)\s+\w+)|(?:[a-záéíóúñ]+))\s+no\s+(.+)", frase, re.I
    )
    if negacion_interna:
        sujeto_local, accion = negacion_interna.groups()
        return Expresion("¬", (leer_expresion(f"{sujeto_local} {accion}", sujeto_local),))

    if re.match(r"^no\s+", frase, re.I):
        return Expresion("¬", (leer_expresion(frase[3:], sujeto),))
    if re.search(r"\bno\b", frase, re.I):
        raise ReglaInvalida("No se pudo interpretar a qué afecta la negación.")

    if re.search(r"\b(?:y|o)\b", frase, re.I):
        raise ReglaInvalida("Hay un conector que no pudo analizarse.")
    return Expresion("atomo", frase=recuperar_sujeto(frase, sujeto))


def escribir_formula(expresion, identificador):
    if expresion.tipo == "atomo":
        return identificador(expresion.frase)
    if expresion.tipo == "¬":
        sub = expresion.hijos[0]
        texto = escribir_formula(sub, identificador)
        return f"¬({texto})" if sub.tipo in {"∧", "∨", "→"} else f"¬{texto}"
    piezas = []
    for sub in expresion.hijos:
        texto = escribir_formula(sub, identificador)
        if sub.tipo in {"∧", "∨", "→"} and (expresion.tipo == "→" or sub.tipo != expresion.tipo):
            texto = f"({texto})"
        piezas.append(texto)
    return f" {expresion.tipo} ".join(piezas)


class CuadernoLogico:
    def __init__(self):
        self.atomos = {}
        self.reglas = []
        self._por_texto = {}

    def anadir(self, texto):
        original = limpiar(texto)
        if not original:
            raise ReglaInvalida("La regla no puede estar vacía.")
        estructura = leer_expresion(original)
        # La asignación se hace en una copia: una regla rechazada no cambia el cuaderno.
        atomos = self.atomos.copy()
        claves = self._por_texto.copy()

        def codigo(frase):
            clave = limpiar(frase).casefold()
            if clave not in claves:
                clave_nueva = f"X{len(atomos) + 1}"
                claves[clave] = clave_nueva
                atomos[clave_nueva] = frase
            return claves[clave]

        simbolica = escribir_formula(estructura, codigo)
        numero = f"R{len(self.reglas) + 1}"
        self.atomos, self._por_texto = atomos, claves
        self.reglas.append({"id": numero, "original": original, "formula": simbolica})
        return simbolica
