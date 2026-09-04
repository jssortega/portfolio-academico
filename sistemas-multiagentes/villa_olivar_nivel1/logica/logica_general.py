def printColor(msg, color):
    colores = {
        "rojo": "\033[91m",
        "verde": "\033[38;5;34m",
        "azul": "\033[94m",
        "amarillo": "\033[93m"
    }
    reset = "\033[0m"
    print(f"{colores.get(color, '')}{msg}{reset}")