from scripts.qa.protected_files import verify_manifests


def test_manifests_integrity():
    # a) all manifest-listed files exist or are explicitly recorded as "not present"
    # Actually, we want to ensure no mismatches exist in the manifests
    results = verify_manifests()
    for manifest, items in results.items():
        if isinstance(items, dict) and "status" in items and items["status"] == "not present":
            # the manifest itself is not present, that's okay for WHATIF if it wasn't created, 
            # but we expect all 3 to be present.
            assert False, f"Manifest {manifest} is missing."
        for path_str, status in items.items():
            assert "mismatch" not in status, f"File {path_str} in {manifest} has been modified (mismatch)!"
            assert "not present" not in status, f"File {path_str} in {manifest} is missing!"

def test_guard_protected_files_diff():
    # (b) a guard that fails if git diff against the freeze commits shows changes to a protected file since the freeze
    # (compare current file hashes with manifest hashes)
    results = verify_manifests()
    for manifest, items in results.items():
        if isinstance(items, dict) and "status" in items and items["status"] == "not present":
            continue
        for path_str, status in items.items():
            assert "mismatch" not in status, f"Protected file {path_str} has changed since freeze ({manifest})!"
