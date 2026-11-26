"""
Genera una imagen QR que apunta a la dirección de tu app de votación.

Cómo usarlo:
1. Averigua la IP local de tu computador (ver instrucciones en el README).
2. Ejecuta:  python generar_qr.py 192.168.1.15
3. Se creará el archivo qr_votacion.png. Imprímelo o muéstralo en una pantalla
   grande para que la gente lo escanee con la cámara de su teléfono.
"""
import sys

import qrcode


def main():
    if len(sys.argv) != 2:
        print("Uso: python generar_qr.py <IP_DE_TU_COMPUTADOR>")
        print("Ejemplo: python generar_qr.py 192.168.1.15")
        sys.exit(1)

    ip = sys.argv[1]
    url = f"http://{ip}:8000/"

    img = qrcode.make(url)
    img.save("qr_votacion.png")
    print(f"Listo. El QR apunta a: {url}")
    print("Se guardó como qr_votacion.png")


if __name__ == "__main__":
    main()
