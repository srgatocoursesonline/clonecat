import os
import sqlite3
import shutil
from pathlib import Path
from src.utils.cache_manager import CacheManager

def test_clear_all_temp_files():
    temp_dir = Path('temp_test_storage/cache')
    temp_dir.mkdir(parents=True, exist_ok=True)
    db_path = temp_dir.parent / 'cache.db'
    # Cria um banco dummy
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()  # Fechar antes de remover!
    # Instancia o CacheManager
    cache_manager = CacheManager(db_path=str(db_path), cache_dir=temp_dir)
    # Chama a limpeza
    confirm = input("\nDeseja limpar os arquivos temporários? (s/n): ").lower()
    if confirm == 's':
        cache_manager.clear_all_temp_files()
        print("Arquivos temporários removidos com sucesso!")
    else:
        print("Operação cancelada.")
    # Verifica se a pasta foi removida
    assert not temp_dir.parent.exists(), 'A pasta temporária não foi removida!'
    print('Teste de limpeza de arquivos temporários passou!')

if __name__ == '__main__':
    test_clear_all_temp_files() 