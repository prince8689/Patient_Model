import urllib.request
import zipfile
import hashlib
import json
import os
import ssl

def main():
    url = "https://ndownloader.figshare.com/files/42966622"
    out_dir = "data/external/shanghai_t2dm"
    zip_path = os.path.join(out_dir, "diabetes_datasets.zip")
    manifest_path = os.path.join(out_dir, "MANIFEST.json")
    
    os.makedirs(out_dir, exist_ok=True)
    
    print("Downloading ShanghaiT2DM dataset from Figshare...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if not os.path.exists(zip_path):
        with urllib.request.urlopen(url, context=ctx) as response, open(zip_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print("Download complete.")
    else:
        print("Dataset already downloaded.")
    
    print("Computing SHA256...")
    hasher = hashlib.sha256()
    with open(zip_path, 'rb') as f:
        hasher.update(f.read())
    sha256_hash = hasher.hexdigest()
    
    print("Extracting files...")
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(out_dir)
        extracted_files = zip_ref.namelist()
        
    manifest = {
        "diabetes_datasets.zip_sha256": sha256_hash,
        "files": extracted_files
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Manifest written to {manifest_path}")
    print("\nLicense Information:")
    print("CC BY 4.0: https://creativecommons.org/licenses/by/4.0/")

if __name__ == "__main__":
    main()
