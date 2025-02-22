import os
import shutil

def delete_collection():
    chroma_db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "chroma_db")
    try:
        if os.path.exists(chroma_db_dir):
            for filename in os.listdir(chroma_db_dir):
                file_path = os.path.join(chroma_db_dir, filename)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                
            print(f"All files and directories inside '{chroma_db_dir}' have been deleted.")
        else:
            print(f"The directory '{chroma_db_dir}' does not exist.")
    except Exception as e:
        print(f"Exception while deleting collection : {e}")
        raise