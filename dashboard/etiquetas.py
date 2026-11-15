"""Etiquetas de presentación que conservan los valores originales del estudio."""

NOMBRES = {
    "A00-B99": "Enfermedades infecciosas y parasitarias",
    "C00-D48": "Tumores y neoplasias",
    "D50-D89": "Enfermedades de la sangre y trastornos de la inmunidad",
    "E00-E90": "Enfermedades endocrinas, nutricionales y metabólicas",
    "F00-F99": "Trastornos mentales y del comportamiento",
    "G00-G99": "Enfermedades del sistema nervioso",
    "H00-H59": "Enfermedades del ojo y sus anexos",
    "H60-H95": "Enfermedades del oído y de la apófisis mastoides",
    "I00-I99": "Enfermedades del sistema circulatorio",
    "J00-J99": "Enfermedades del sistema respiratorio",
    "K00-K93": "Enfermedades del sistema digestivo",
    "L00-L99": "Enfermedades de la piel y del tejido subcutáneo",
    "M00-M99": "Enfermedades del sistema osteomuscular y del tejido conjuntivo",
    "N00-N99": "Enfermedades del sistema genitourinario",
    "O00-O99": "Embarazo, parto y puerperio",
    "P00-P96": "Afecciones originadas en el período perinatal",
    "Q00-Q99": "Malformaciones congénitas y anomalías cromosómicas",
    "R00-R99": "Síntomas, signos y hallazgos anormales no clasificados en otra parte",
    "S00-T98": "Traumatismos, envenenamientos y otras consecuencias de causas externas",
    "U00-U99": "Códigos para propósitos especiales",
    "Z00-Z99": "Factores que influyen en el estado de salud y contacto con servicios de salud",
}


ESTABLECIMIENTOS = {
    "SNSS": "SNSS — Red de servicios de salud",
    "No SNSS": "No SNSS — Fuera de la red SNSS",
}


def etiqueta(variable: str, valor: str) -> str:
    if variable == "capitulo":
        nombre = NOMBRES.get(valor)
        return f"{valor} — {nombre}" if nombre else valor
    if variable == "establecimiento":
        return ESTABLECIMIENTOS.get(valor, valor)
    return valor


def opciones(variable: str, valores) -> dict[str, str]:
    return {valor: etiqueta(variable, valor) for valor in valores}
