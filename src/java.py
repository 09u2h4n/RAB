import os
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple

from tools import download_file

class JavaController:
    """Controller for downloading and installing Java."""
    
    JAVA_DOWNLOADS = {
        "windows": {
            "11": "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip",
            "17": "https://download.java.net/java/GA/jdk17/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-17_windows-x64_bin.zip",
            "21": "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_windows-x64_bin.zip"
        },
        "linux": {
            "11": "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_linux-x64_bin.tar.gz",
            "17": "https://download.java.net/java/GA/jdk17/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-17_linux-x64_bin.tar.gz",
            "21": "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_linux-x64_bin.tar.gz"
        },
        "darwin": {
            "11": "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_osx-x64_bin.tar.gz",
            "17": "https://download.java.net/java/GA/jdk17/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-17_macos-x64_bin.tar.gz",
            "21": "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_macos-x64_bin.tar.gz"
        }
    }

    def __init__(self):
        """Initialize JavaController with system-specific settings."""
        self.system = platform.system().lower()
        self.downloads_dir = Path.home() / "Downloads" / "java"
        self.installation_dir = Path.home() / "java"
        self.current_java_path: Optional[Path] = None

    def check_existing_java(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if Java is already installed and get its version.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (Is Java installed, Version if found, Installation path if found)
        """
        # Check JAVA_HOME first
        java_home = os.environ.get('JAVA_HOME')
        if java_home and Path(java_home).exists():
            version = self._get_java_version(Path(java_home) / 'bin' / 'java')
            if version:
                return True, version, java_home

        # Check PATH for java executable
        java_cmd = 'java.exe' if self.system == 'windows' else 'java'
        
        try:
            # Try 'which' on Unix or 'where' on Windows
            if self.system == 'windows':
                result = subprocess.run(['where', java_cmd], capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(['which', java_cmd], capture_output=True, text=True, check=True)
            
            java_path = result.stdout.strip().split('\n')[0]
            if java_path:
                version = self._get_java_version(Path(java_path))
                if version:
                    # Get installation directory from binary path
                    install_path = str(Path(java_path).parent.parent)
                    return True, version, install_path
                    
        except subprocess.CalledProcessError:
            pass
        
        # Check common installation directories
        common_paths = self._get_common_java_paths()
        for path in common_paths:
            if path.exists():
                java_bin = path / 'bin' / java_cmd
                if java_bin.exists():
                    version = self._get_java_version(java_bin)
                    if version:
                        return True, version, str(path)

        return False, None, None

    def _get_java_version(self, java_path: Path) -> Optional[str]:
        """
        Get Java version from a specific java executable.
        
        Args:
            java_path (Path): Path to java executable
            
        Returns:
            Optional[str]: Version string if found, None otherwise
        """
        try:
            result = subprocess.run(
                [str(java_path), '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            # Version info is typically in stderr for Java
            version_output = result.stderr or result.stdout
            
            # Parse version string
            for line in version_output.split('\n'):
                if 'version' in line.lower():
                    # Extract version number (handles both formats: 1.8.0_311 and 11.0.2)
                    parts = line.split('"')[1].split('.')
                    if parts[0] == '1':
                        return parts[1]  # For Java 8 and below
                    return parts[0]      # For Java 9+
                    
        except (subprocess.CalledProcessError, IndexError, KeyError):
            return None
            
        return None

    def _get_common_java_paths(self) -> list[Path]:
        """Get list of common Java installation paths for current OS."""
        paths = []
        
        if self.system == 'windows':
            program_files = [
                os.environ.get('ProgramFiles'),
                os.environ.get('ProgramFiles(x86)'),
                os.environ.get('ProgramW6432')
            ]
            for pf in program_files:
                if pf:
                    paths.extend([
                        Path(pf) / 'Java',
                        Path(pf) / 'AdoptOpenJDK',
                        Path(pf) / 'OpenJDK',
                        Path(pf) / 'Amazon Corretto'
                    ])
                    
        elif self.system == 'darwin':
            paths.extend([
                Path('/Library/Java/JavaVirtualMachines'),
                Path('/System/Library/Java/JavaVirtualMachines')
            ])
            
        else:  # linux
            paths.extend([
                Path('/usr/lib/jvm'),
                Path('/usr/java'),
                Path('/opt/java'),
                Path('/opt/openjdk')
            ])
            
        return paths

    def download_java(self, version: str = "11", force: bool = False) -> Tuple[bool, str]:
        """
        Download Java for the current operating system if not already installed.
        
        Args:
            version (str): Java version to download (11, 17, or 21)
            force (bool): Force download even if Java is already installed
            
        Returns:
            Tuple[bool, str]: (Success status, Message or error description)
        """
        # Check for existing Java installation
        if not force:
            installed, existing_version, path = self.check_existing_java()
            if installed:
                return False, f"Java {existing_version} is already installed at {path}. Use force=True to download anyway."

        try:
            # Validate version
            if version not in self.JAVA_DOWNLOADS[self.system]:
                return False, f"Unsupported Java version: {version}"

            # Create downloads directory if it doesn't exist
            self.downloads_dir.mkdir(parents=True, exist_ok=True)

            # Get download URL for current system and version
            download_url = self.JAVA_DOWNLOADS[self.system][version]
            filename = download_url.split('/')[-1]
            download_path = self.downloads_dir / filename

            # Download Java if not already downloaded
            if not download_path.exists():
                success = download_file(download_url, str(download_path))
                if not success:
                    return False, f"Failed to download Java {version}"

            self.current_java_path = download_path
            return True, f"Successfully downloaded Java {version}"

        except Exception as e:
            return False, f"Error downloading Java: {str(e)}"

    def install_java(self, force: bool = False) -> Tuple[bool, str]:
        """
        Install the downloaded Java version if not already installed.
        
        Args:
            force (bool): Force installation even if Java is already installed
            
        Returns:
            Tuple[bool, str]: (Success status, Message or error description)
        """
        # Check for existing Java installation
        if not force:
            installed, existing_version, path = self.check_existing_java()
            if installed:
                return False, f"Java {existing_version} is already installed at {path}. Use force=True to install anyway."

        if not self.current_java_path or not self.current_java_path.exists():
            return False, "No Java download found. Please download Java first."

        try:
            # Create installation directory
            self.installation_dir.mkdir(parents=True, exist_ok=True)

            # Extract based on file type
            if self.current_java_path.suffix == '.zip':
                self._extract_zip()
            elif self.current_java_path.suffix == '.gz':
                self._extract_tar_gz()
            else:
                return False, f"Unsupported archive format: {self.current_java_path.suffix}"

            # Set environment variables
            self._set_environment_variables()

            # Verify installation
            if self._verify_installation():
                return True, "Java installed successfully"
            return False, "Java installation verification failed"

        except Exception as e:
            return False, f"Error installing Java: {str(e)}"

    def _extract_zip(self) -> None:
        """Extract ZIP archive on Windows."""
        import zipfile
        with zipfile.ZipFile(self.current_java_path, 'r') as zip_ref:
            zip_ref.extractall(self.installation_dir)

    def _extract_tar_gz(self) -> None:
        """Extract TAR.GZ archive on Unix-like systems."""
        import tarfile
        with tarfile.open(self.current_java_path, 'r:gz') as tar_ref:
            tar_ref.extractall(self.installation_dir)

    def _set_environment_variables(self) -> None:
        """Set JAVA_HOME and update PATH environment variable."""
        # Find JDK directory
        jdk_dir = next(self.installation_dir.glob("jdk*"))

        if self.system == "windows":
            # Set environment variables on Windows
            subprocess.run(['setx', 'JAVA_HOME', str(jdk_dir)], check=True)
            subprocess.run(['setx', 'PATH', f"%PATH%;%JAVA_HOME%\\bin"], check=True)
        else:
            # Set environment variables on Unix-like systems
            shell = os.environ.get('SHELL', '/bin/bash')
            profile_file = Path.home() / ('.zshrc' if 'zsh' in shell else '.bashrc')

            with profile_file.open('a') as f:
                f.write(f'\nexport JAVA_HOME="{jdk_dir}"\n')
                f.write('export PATH="$JAVA_HOME/bin:$PATH"\n')

    def _verify_installation(self) -> bool:
        """
        Verify Java installation by checking 'java -version'.

        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            result = subprocess.run(
                ['java', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            return 'version' in result.stderr.lower()
        except subprocess.CalledProcessError:
            return False

    def cleanup(self) -> None:
        """Clean up downloaded files."""
        try:
            if self.downloads_dir.exists():
                shutil.rmtree(self.downloads_dir)
        except Exception:
            pass

if __name__ == "__main__":
    # Create controller instance
    java_ctrl = JavaController()

    # Download Java (version 11 by default)
    success, message = java_ctrl.download_java()
    if success:
        print("Download successful")
        
        # Install Java
        success, message = java_ctrl.install_java()
        if success:
            print("Installation successful")
        else:
           print(f"Installation failed: {message}")
    else:
        print(f"Download failed: {message}")

    # Optional cleanup
    java_ctrl.cleanup()
