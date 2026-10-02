import pytest

from scripts.qa.config_audit import audit_config


def test_config_audit_passes_with_current():
    # Should pass because current config only has safe additions
    assert audit_config()

def test_config_audit_fails_on_frozen_section_change(monkeypatch):
    from scripts.qa.config_audit import get_current_config
    current = get_current_config()
    
    # Modify a frozen-relevant value
    current["random_seed"] = 9999
    
    with pytest.raises(ValueError, match="Config audit failed: Frozen section 'random_seed' has been modified."):
        audit_config(current)

def test_config_audit_allows_app_key(monkeypatch):
    from scripts.qa.config_audit import get_current_config
    current = get_current_config()
    
    # Add a new key to the allowed 'app' section
    if "app" not in current:
        current["app"] = {}
    current["app"]["new_test_key"] = "safe"
    
    # Should not raise
    assert audit_config(current)
    
def test_config_audit_fails_on_unknown_new_section(monkeypatch):
    from scripts.qa.config_audit import get_current_config
    current = get_current_config()
    
    current["evil_new_section"] = {"malicious": True}
    
    with pytest.raises(ValueError, match="Config audit failed: New section 'evil_new_section' is not in the allowed list"):
        audit_config(current)
