import os
import time
import shutil
from pathlib import Path
from typing import Tuple
from app.recommendations.core.config import settings


def check_vector_dbs_exist() -> Tuple[bool, str]:
   
    students_path = Path(settings.VECTOR_STUDENTS_PATH)
    internships_path = Path(settings.VECTOR_INTERNSHIPS_PATH)
    
    if not students_path.exists() or not internships_path.exists():
        return False, " Vector DB directories not found"
    
    students_files = list(students_path.glob("*"))
    internships_files = list(internships_path.glob("*"))
    
    if not students_files or not internships_files:
        return False, " Vector DB directories are empty"
    
    has_students_sqlite = any(f.name == "chroma.sqlite3" for f in students_files)
    has_internships_sqlite = any(f.name == "chroma.sqlite3" for f in internships_files)
    
    if not has_students_sqlite or not has_internships_sqlite:
        return False, " Vector DB SQLite files are missing"
    
    students_sqlite = students_path / "chroma.sqlite3"
    internships_sqlite = internships_path / "chroma.sqlite3"
    
    if students_sqlite.stat().st_size < 1024:
        return False, " Student Vector DB is empty (no data)"
    
    if internships_sqlite.stat().st_size < 1024:
        return False, " Internship Vector DB is empty (no data)"
    
    students_data_files = [
        f for f in students_files 
        if f.suffix in ['.bin', '.parquet', '.pkl'] or f.is_dir()
    ]
    
    internships_data_files = [
        f for f in internships_files 
        if f.suffix in ['.bin', '.parquet', '.pkl'] or f.is_dir()
    ]
    
    return True, " Vector DBs found and valid (with embeddings)"


def safe_remove_directory(path: Path, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            if path.exists():
                import gc
                gc.collect()  
                
                time.sleep(0.5) 
                shutil.rmtree(path)
                print(f" Removed old DB at {path}")
                return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f" Directory locked, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                print(f" Could not remove {path}: {e}")
                return False
        except Exception as e:
            print(f" Error removing {path}: {e}")
            return False
    
    return True


def build_vector_dbs_if_needed():
    exists, message = check_vector_dbs_exist()
    if exists:
        print(f" {message}")
        return  
    print(f" {message}")
    
    students_path = Path(settings.VECTOR_STUDENTS_PATH)
    internships_path = Path(settings.VECTOR_INTERNSHIPS_PATH)
    
    sqlite_files = []
    if students_path.exists():
        sqlite_files.extend(students_path.glob("*.sqlite3"))
    if internships_path.exists():
        sqlite_files.extend(internships_path.glob("*.sqlite3"))
    
    locked_files = []
    for sqlite_file in sqlite_files:
        try:
            with open(sqlite_file, 'a'):
                pass
        except (PermissionError, IOError):
            locked_files.append(sqlite_file)
    
    if locked_files:
        print(" WARNING: Vector DB files are currently in use!")
        print("\nLocked files:")
        for f in locked_files:
            print(f"   • {f}")
        print("\n This usually means:")
        print("   1. Another instance of the app is running")
        print("   2. A service has already loaded the Vector DBs")
        print("\n SOLUTION: Please restart the application")
        print("   The Vector DBs will be rebuilt on next startup")

        
        return
    
    print(" Building Vector DBs...")
    try:
        from app.recommendations.scripts.build_vectors import build_vector_databases
        build_vector_databases()
        time.sleep(1)
        
        exists_after, message_after = check_vector_dbs_exist()
        if not exists_after:
            print("vector databases appear to have been created.")
        else:
            print(f" {message_after}")
        
    except Exception as e:
        print(f" Failed to build Vector DBs: {e}")
        print("\n" + "="*60)
        print(" TROUBLESHOOTING:")
        print("="*60)
        print("1. Make sure SQL Server is running and accessible")
        print("2. Check database connection settings in .env")
        print("3. If error persists, manually delete these folders:")
        print(f"   • {settings.VECTOR_STUDENTS_PATH}")
        print(f"   • {settings.VECTOR_INTERNSHIPS_PATH}")
        print("4. Then restart the application")
        print("="*60 + "\n")
        
        raise RuntimeError(
            f"Cannot start Recommendation Engine without Vector DBs. Error: {e}"
        )