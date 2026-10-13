"""
Installer module for Windows AI Agent
Handles dependency installation, environment setup, and optional EXE packaging.
"""

from __future__ import annotations

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Tuple


class Installer:
    """Installs prerequisites and sets up the Windows AI Agent environment."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.requirements = self.project_root / "requirements.txt"
        self.python = sys.executable

    def run(self, upgrade: bool = True, create_exe: bool = False) -> bool:
        print("=" * 60)
        print("Windows AI Agent - Installer")
        print("=" * 60)

        if not self._ensure_pip():
            return False

        if not self._install_requirements(upgrade=upgrade):
            return False

        if create_exe:
            self._build_exe()

        self._create_launcher_scripts()
        print("\n[SUCCESS] Installation complete.")
        print(f"Project root: {self.project_root}")
        print("Run the agent with:  python -m src.main   or use run_agent.bat")
        return True

    def _ensure_pip(self) -> bool:
        print("\n[1/4] Ensuring pip is available...")
        try:
            result = subprocess.run(
                [self.python, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=20
            )
            if result.returncode != 0:
                print("  pip not found. Attempting ensurepip...")
                subprocess.check_call([self.python, "-m", "ensurepip", "--upgrade"])
            print("  pip OK")
            return True
        except Exception as e:
            print(f"  FAILED to set up pip: {e}")
            return False

    def _install_requirements(self, upgrade: bool = True) -> bool:
        print("\n[2/4] Installing Python packages from requirements.txt...")
        if not self.requirements.exists():
            print(f"  WARNING: {self.requirements} not found. Installing core packages only.")
            packages = ["rich", "psutil", "requests", "python-dotenv", "pywin32", "openai"]
            cmd = [self.python, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(packages)
        else:
            cmd = [self.python, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(["-r", str(self.requirements)])

        try:
            subprocess.check_call(cmd)
            print("  Packages installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  FAILED to install packages: {e}")
            print("  Try running as Administrator or check your internet connection.")
            return False

    def _build_exe(self) -> None:
        print("\n[3/4] Building standalone executable with PyInstaller...")
        try:
            # Ensure pyinstaller is installed
            subprocess.check_call([self.python, "-m", "pip", "install", "--upgrade", "pyinstaller"])

            main_script = self.project_root / "src" / "main.py"
            if not main_script.exists():
                print("  main.py not found, skipping EXE build.")
                return

            dist_dir = self.project_root / "dist"
            build_dir = self.project_root / "build"

            cmd = [
                self.python, "-m", "PyInstaller",
                "--noconfirm",
                "--onefile",
                "--console",
                "--name", "WindowsAIAgent",
                "--distpath", str(dist_dir),
                "--workpath", str(build_dir),
                str(main_script),
            ]
            subprocess.check_call(cmd)
            print(f"  EXE created at: {dist_dir / 'WindowsAIAgent.exe'}")
        except Exception as e:
            print(f"  EXE build failed (non-fatal): {e}")
            print("  You can still run the agent with Python.")

    def _create_launcher_scripts(self) -> None:
        print("\n[4/4] Creating launcher scripts...")

        # run_agent.bat
        bat_content = f"""@echo off
title Windows AI Agent
cd /d "%~dp0"
"{self.python}" -m src.main %*
if errorlevel 1 pause
"""
        bat_path = self.project_root / "run_agent.bat"
        bat_path.write_text(bat_content, encoding="utf-8")
        print(f"  Created: {bat_path.name}")

        # check_prereqs.bat
        check_bat = f"""@echo off
title Windows AI Agent - Prerequisite Check
cd /d "%~dp0"
"{self.python}" -m src.prereq_checker
pause
"""
        check_path = self.project_root / "check_prereqs.bat"
        check_path.write_text(check_bat, encoding="utf-8")
        print(f"  Created: {check_path.name}")

        # install.bat
        install_bat = f"""@echo off
title Windows AI Agent - Installer
cd /d "%~dp0"
echo Installing Windows AI Agent dependencies...
"{self.python}" -m src.installer
pause
"""
        install_path = self.project_root / "install.bat"
        install_path.write_text(install_bat, encoding="utf-8")
        print(f"  Created: {install_path.name}")

        # build_exe.bat
        build_bat = f"""@echo off
title Windows AI Agent - Build EXE
cd /d "%~dp0"
echo Building standalone EXE (this may take a few minutes)...
"{self.python}" -m src.installer --exe
pause
"""
        build_path = self.project_root / "build_exe.bat"
        build_path.write_text(build_bat, encoding="utf-8")
        print(f"  Created: {build_path.name}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Windows AI Agent Installer")
    parser.add_argument("--exe", action="store_true", help="Also build a standalone EXE")
    parser.add_argument("--no-upgrade", action="store_true", help="Do not upgrade existing packages")
    args = parser.parse_args()

    installer = Installer()
    success = installer.run(upgrade=not args.no_upgrade, create_exe=args.exe)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
