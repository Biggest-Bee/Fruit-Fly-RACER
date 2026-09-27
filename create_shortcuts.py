"""
Create Desktop Shortcuts for Fruit Fly AI
This script creates desktop and start menu shortcuts for the application
"""

import os
import sys
import subprocess
from pathlib import Path

def create_windows_shortcut():
    """Create shortcuts on Windows"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Get paths
        project_dir = Path(__file__).parent.absolute()
        script_path = project_dir / "desktop_app" / "main_app.py"
        python_exe = sys.executable
        icon_path = project_dir / "icon.ico"
        
        # Desktop shortcut
        desktop = Path(os.path.expanduser("~/Desktop"))
        desktop_shortcut = desktop / "Fruit Fly AI.lnk"
        
        # Start menu shortcut
        start_menu = Path(os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"))
        start_menu_shortcut = start_menu / "Fruit Fly AI.lnk"
        
        if not start_menu.exists():
            start_menu.mkdir(parents=True, exist_ok=True)
        
        # Create desktop shortcut
        if script_path.exists():
            shell = Dispatch('WScript.Shell')
            
            # Desktop shortcut
            shortcut = shell.CreateShortCut(str(desktop_shortcut))
            shortcut.Targetpath = python_exe
            shortcut.Arguments = f'"{script_path}"'
            shortcut.WorkingDirectory = str(project_dir)
            
            if icon_path.exists():
                shortcut.IconLocation = str(icon_path)
            
            shortcut.Description = "Fruit Fly AI - Desktop Application"
            shortcut.save()
            print(f"[OK] Desktop shortcut created: {desktop_shortcut}")
            
            # Start menu shortcut
            shortcut = shell.CreateShortCut(str(start_menu_shortcut))
            shortcut.Targetpath = python_exe
            shortcut.Arguments = f'"{script_path}"'
            shortcut.WorkingDirectory = str(project_dir)
            
            if icon_path.exists():
                shortcut.IconLocation = str(icon_path)
            
            shortcut.Description = "Fruit Fly AI - Desktop Application"
            shortcut.save()
            print(f"[OK] Start menu shortcut created: {start_menu_shortcut}")
            
            return True
        else:
            print(f"[ERROR] Script not found: {script_path}")
            return False
            
    except ImportError as e:
        print(f"[ERROR] Required libraries not installed: {e}")
        print("Install with: pip install pywin32 winshell")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating shortcuts: {e}")
        return False

def create_mac_shortcut():
    """Create application bundle on macOS"""
    try:
        project_dir = Path(__file__).parent.absolute()
        script_path = project_dir / "desktop_app" / "main_app.py"
        
        # Create .app bundle structure
        app_name = "Fruit Fly AI.app"
        app_path = Path(os.path.expanduser("~/Desktop")) / app_name
        
        if app_path.exists():
            print(f"[WARNING] Application already exists: {app_path}")
            return False
        
        # Create app bundle structure
        contents = app_path / "Contents"
        macos = contents / "MacOS"
        resources = contents / "Resources"
        
        for folder in [contents, macos, resources]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Create Info.plist
        info_plist = contents / "Info.plist"
        info_plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher.sh</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleName</key>
    <string>Fruit Fly AI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>""")
        
        # Create launcher script
        launcher = macos / "launcher.sh"
        launcher.write_text(f"""#!/bin/bash
cd "{project_dir}"
python3 desktop_app/main_app.py
""")
        launcher.chmod(0o755)
        
        print(f"[OK] macOS app bundle created: {app_path}")
        print("Note: You'll need to create an icon.icns file in Resources/")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating macOS app: {e}")
        return False

def create_linux_shortcut():
    """Create .desktop file on Linux"""
    try:
        project_dir = Path(__file__).parent.absolute()
        script_path = project_dir / "desktop_app" / "main_app.py"
        
        # Desktop shortcut
        desktop = Path(os.path.expanduser("~/Desktop"))
        desktop_shortcut = desktop / "fruit-fly-ai.desktop"
        
        # Applications menu shortcut
        applications = Path(os.path.expanduser("~/.local/share/applications"))
        applications_shortcut = applications / "fruit-fly-ai.desktop"
        
        if not applications.exists():
            applications.mkdir(parents=True, exist_ok=True)
        
        # Create .desktop file content
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Fruit Fly AI
Comment=Simulated fruit fly brain with coding training
Exec=python3 {script_path}
Icon={project_dir}/icon.ico
Terminal=false
Categories=Development;Education;Science;
"""
        
        # Write desktop shortcut
        desktop_shortcut.write_text(desktop_content)
        desktop_shortcut.chmod(0o755)
        print(f"[OK] Desktop shortcut created: {desktop_shortcut}")
        
        # Write applications menu shortcut
        applications_shortcut.write_text(desktop_content)
        applications_shortcut.chmod(0o755)
        print(f"[OK] Applications menu shortcut created: {applications_shortcut}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating Linux shortcuts: {e}")
        return False

def main():
    """Main function to create shortcuts based on OS"""
    print("Creating desktop shortcuts for Fruit Fly AI...")
    print(f"Operating System: {sys.platform}")
    
    if sys.platform == "win32":
        success = create_windows_shortcut()
    elif sys.platform == "darwin":
        success = create_mac_shortcut()
    elif sys.platform.startswith("linux"):
        success = create_linux_shortcut()
    else:
        print(f"[ERROR] Unsupported platform: {sys.platform}")
        success = False
    
    if success:
        print("\n[SUCCESS] Shortcuts created successfully!")
        print("You can now find Fruit Fly AI in:")
        print("- Desktop")
        print("- Start Menu / Applications")
        print("The app will also be searchable in Windows Search / Spotlight")
    else:
        print("\n[ERROR] Failed to create shortcuts")
        print("You can still run the app with: python desktop_app/main_app.py")

if __name__ == "__main__":
    main()