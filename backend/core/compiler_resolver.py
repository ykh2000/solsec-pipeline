import re
import subprocess
import sys
import os

class CompilerResolver:
    """
    Utility class to parse pragma statements in Solidity files
    and dynamically switch the solc version using solc-select.
    """

    @staticmethod
    def resolve_and_switch(file_path: str):
        """
        Parses the Solidity contract file pragma statement and uses
        solc-select to switch the active global solc version.
        """
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        # Find the pragma solidity statement
        match = re.search(r"pragma\s+solidity\s+([^;]+);", content)
        if not match:
            # Default fallback to 0.8.0 if no pragma found
            CompilerResolver._switch_to_version("0.8.0")
            return

        pragma_val = match.group(1).strip()
        
        # Extract version numbers like 0.8.0, 0.4.24
        version_matches = re.findall(r"\d+\.\d+\.\d+", pragma_val)
        if not version_matches:
            CompilerResolver._switch_to_version("0.8.0")
            return

        target_version = version_matches[0]
        
        # Get available versions from solc-select
        installed_versions = CompilerResolver._get_installed_versions()
        
        if target_version in installed_versions:
            CompilerResolver._switch_to_version(target_version)
        else:
            # Prefix matching (e.g. 0.8.0 -> matches 0.8.x)
            prefix = ".".join(target_version.split(".")[:2])
            for v in installed_versions:
                if v.startswith(prefix):
                    CompilerResolver._switch_to_version(v)
                    return
            # If not installed, fallback to 0.8.0
            CompilerResolver._switch_to_version("0.8.0")

    @staticmethod
    def _get_installed_versions():
        try:
            solc_select_path = CompilerResolver._get_solc_select_path()
            result = subprocess.run([solc_select_path, "versions"], capture_output=True, text=True)
            versions = []
            for line in result.stdout.splitlines():
                if line.strip():
                    v = line.split()[0]
                    versions.append(v)
            return versions
        except Exception:
            return ["0.8.0"]

    @staticmethod
    def _switch_to_version(version: str):
        try:
            solc_select_path = CompilerResolver._get_solc_select_path()
            # print(f"[CompilerResolver] Switched to version {version}")
            subprocess.run([solc_select_path, "use", version], check=True, capture_output=True)
        except Exception as e:
            # Fail silently, print to stderr
            sys.stderr.write(f"[CompilerResolver] Failed to switch to version {version}: {e}\n")

    @staticmethod
    def _get_solc_select_path():
        venv_bin_dir = os.path.dirname(sys.executable)
        solc_select_path = os.path.join(venv_bin_dir, "solc-select")
        if os.path.exists(solc_select_path):
            return solc_select_path
        return "solc-select"
