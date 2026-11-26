"""Demostración no destructiva de respaldo y recuperación de una base SQLite.
Detener la aplicación antes de ejecutar. Usar exclusivamente datos ficticios.
"""
import argparse
import hashlib
import shutil
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def comprobar_sqlite(path):
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as conn:
        if conn.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise RuntimeError('La comprobación de integridad SQLite falló')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--origen', type=Path, default=Path(__file__).with_name('tecnohogar.db'))
    p.add_argument('--destino', type=Path, required=True)
    args = p.parse_args()
    origen = args.origen.resolve(strict=True)
    destino = args.destino.resolve()
    if not origen.is_file() or origen.stat().st_size == 0:
        p.error('El origen debe ser un archivo existente y no vacío')
    if destino == origen.parent or origen.parent in destino.parents:
        p.error('Usa un destino fuera de la carpeta de origen, preferentemente otra unidad')
    if any(Path(str(origen) + suf).exists() for suf in ('-wal', '-journal')):
        p.error('Hay archivos de transacción SQLite: cierra la aplicación y verifica la base antes de copiarla')
    comprobar_sqlite(origen)
    destino.mkdir(parents=True, exist_ok=True)
    carpeta = Path(tempfile.mkdtemp(prefix='respaldo_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_', dir=destino))
    respaldo = carpeta / origen.name
    huella = sha256(origen)
    shutil.copy2(origen, respaldo)
    huella_respaldo = sha256(respaldo)
    if huella != huella_respaldo or sha256(origen) != huella:
        raise RuntimeError('El respaldo no coincide o el origen cambió durante la copia')
    (carpeta / 'SHA256.txt').write_text(f'{huella}  {origen.name}\n', encoding='utf-8')
    print(f'ORIGEN: {origen} ({origen.stat().st_size} bytes)')
    print(f'RESPALDO: {respaldo} ({respaldo.stat().st_size} bytes)')
    print(f'SHA-256 origen:   {huella}')
    print(f'SHA-256 respaldo: {huella_respaldo}')
    with tempfile.TemporaryDirectory(prefix='simulacion_', dir=origen.parent) as sim:
        trabajo = Path(sim) / origen.name
        shutil.copy2(origen, trabajo)
        trabajo.unlink()  # Eliminar SOLO la copia temporal creada para esta simulación.
        print(f'Pérdida simulada de la copia temporal: {not trabajo.exists()}')
        shutil.copy2(respaldo, trabajo)
        huella_restaurada = sha256(trabajo)
        print(f'RESTAURADO: {trabajo.stat().st_size} bytes')
        print(f'SHA-256 restaurado: {huella_restaurada}')
        comprobar_sqlite(trabajo)
        if huella_restaurada != huella or sha256(origen) != huella:
            raise RuntimeError('La restauración no coincide o el origen cambió')
        print('RESULTADO: hashes coinciden, SQLite integrity_check=ok, original intacto.')
    print('La copia temporal se limpia; el respaldo y su manifiesto se conservan.')
    print('Una carpeta en el mismo disco no protege frente a pérdida de la unidad o ransomware.')


if __name__ == '__main__':
    main()
