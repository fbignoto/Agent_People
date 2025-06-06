import subprocess
import os
from dotenv import load_dotenv

def create_bucket(bucket_name, location, project_id):
    try:
        subprocess.run(
            ["gcloud", "storage", "buckets", "create", f"gs://{bucket_name}", 
                "--location", location, "--project", project_id],
            check=True
        )
        print(f"Bucket {bucket_name} criado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar o bucket: {e}")

def upload_files_to_bucket(bucket_name, folder_path):
    try:
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                subprocess.run(
                    ["gsutil", "cp", file_path, f"gs://{bucket_name}/"],
                    check=True
                )
                print(f"Arquivo {file_name} enviado com sucesso para o bucket {bucket_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar arquivos para o bucket: {e}")
    except FileNotFoundError as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    load_dotenv()

    bucket_name = os.getenv("GCP_BUCKET_NAME")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(current_dir, "bucket_rhaissa")
    
    create_bucket(bucket_name, location, project_id)
    
    upload_files_to_bucket(bucket_name, folder_path)