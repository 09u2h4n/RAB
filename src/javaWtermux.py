class JavaController:
    """Controller for downloading and installing Java."""

    JAVA_DOWNLOADS = {
        "termux": {
            "11": "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_linux-aarch64_bin.tar.gz",
            "17": "https://download.java.net/java/GA/jdk17/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-17_linux-aarch64_bin.tar.gz",
            "21": "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_linux-aarch64_bin.tar.gz"
        },
        # ... rest of the JAVA_DOWNLOADS dictionary remains the same ...
    }

    def __init__(self):
        """Initialize JavaController with system-specific settings."""
        self.system = self._detect_system()
        self.downloads_dir = Path.home() / "downloads" / "java"
        self.installation_dir = Path.home() / "java"
        self.current_java_path: Optional[Path] = None

    def _detect_system(self) -> str:
        """Detect if running on Termux or other systems."""
        system = platform.system().lower()
        if system == "linux" and os.path.exists("/data/data/com.termux"):
            return "termux"
        return system

    def _get_common_java_paths(self) -> list[Path]:
        """Get list of common Java installation paths for current OS."""
        paths = []

        if self.system == 'termux':
            # Termux-specific paths
            prefix = Path("/data/data/com.termux/files")
            paths.extend([
                prefix / "usr" / "lib" / "jvm",
                prefix / "usr" / "java",
                prefix / "home" / "java"
            ])
        elif self.system == 'windows':
            # ... existing Windows paths ...
            pass
        elif self.system == 'darwin':
            # ... existing macOS paths ...
            pass
        else:  # standard linux
            # ... existing Linux paths ...
            pass

        return paths

    def _set_environment_variables(self) -> None:
        """Set JAVA_HOME and update PATH environment variable."""
        # Find JDK directory
        jdk_dir = next(self.installation_dir.glob("jdk*"))

        if self.system == "termux":
            # Set environment variables for Termux
            profile_file = Path.home() / ".profile"
            
            # Create .profile if it doesn't exist
            profile_file.touch(exist_ok=True)
            
            with profile_file.open('a') as f:
                f.write(f'\nexport JAVA_HOME="{jdk_dir}"\n')
                f.write('export PATH="$JAVA_HOME/bin:$PATH"\n')
                
            # Also update current session
            os.environ['JAVA_HOME'] = str(jdk_dir)
            os.environ['PATH'] = f"{jdk_dir}/bin:{os.environ.get('PATH', '')}"
            
        elif self.system == "windows":
            # ... existing Windows code ...
            pass
        else:
            # ... existing Unix-like systems code ...
            pass

    def install_java(self, force: bool = False) -> Tuple[bool, str]:
        """Install the downloaded Java version if not already installed."""
        # ... existing code ...

        try:
            if self.system == "termux":
                # Ensure required packages are installed
                subprocess.run(['pkg', 'update'], check=True)
                subprocess.run(['pkg', 'install', '-y', 'tar', 'gzip'], check=True)

            # ... rest of the installation process ...
            
            # For Termux, we need to set executable permissions
            if self.system == "termux":
                java_bin = next(self.installation_dir.glob("jdk*/bin/java"))
                java_bin.chmod(java_bin.stat().st_mode | 0o111)  # Add executable permission

            # Continue with regular installation steps
            self._set_environment_variables()

            if self._verify_installation():
                return True, "Java installed successfully"
            return False, "Java installation verification failed"

        except Exception as e:
            return False, f"Error installing Java: {str(e)}"
