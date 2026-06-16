import os

from huggingface_hub import snapshot_download


def download_parquet_files(repo_id: str, local_dir: str, hf_token: str = None):
    """
    Downloads only the .parquet files from a specified Hugging Face dataset repository.
    """
    print(f"Starting download for dataset: {repo_id}...")

    # Download files matching the pattern directly to your local folder
    downloaded_path = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",  # Must specify 'dataset' (defaults to 'model')
        local_dir=local_dir,  # Where to save the files on your machine
        allow_patterns=["*.parquet", "**/*.parquet"],  # Only grab parquet files
        token=hf_token,  # Optional: Add your HF token if the dataset is gated/private
    )

    print(f" Successfully downloaded parquet files to: {downloaded_path}")


def download_onnx_models(repo_id: str, local_dir: str, hf_token: str = None):
    """
    Downloads only the .onnx files from a specified Hugging Face model repository.
    """
    print(f"Starting download for model repo: {repo_id}...")

    # Download files matching the pattern directly to your local folder
    downloaded_path = snapshot_download(
        repo_id=repo_id,
        repo_type="model",  # Explicitly setting to 'model' (default)
        local_dir=local_dir,  # Where to save the files on your machine
        allow_patterns=["*.onnx", "**/*.onnx"],  # Only grab ONNX files
        token=hf_token,  # Optional: Add your HF token if the repo is private/gated
    )

    print(f" Successfully downloaded ONNX files to: {downloaded_path}")


if __name__ == "__main__":
    HF_TOKEN = os.getenv("HF_TOKEN")

    REPO_ID = "tonyassi/celebrity-1000"
    LOCAL_DIRECTORY = "./data/celebrities-1000/dataset"
    download_parquet_files(repo_id=REPO_ID, local_dir=LOCAL_DIRECTORY, hf_token=HF_TOKEN)

    REPO_ID = "HITS-AIN/Celebrities"
    LOCAL_DIRECTORY = "./data/celebrities-1000/model"
    download_onnx_models(repo_id=REPO_ID, local_dir=LOCAL_DIRECTORY, hf_token=HF_TOKEN)
