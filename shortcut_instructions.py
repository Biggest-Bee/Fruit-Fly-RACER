"""
Manual Shortcut Creation Instructions
Alternative method if automated script doesn't work
"""

print("""
Manual Shortcut Creation Instructions for Fruit Fly AI
======================================================

WINDOWS:
--------

1. DESKTOP SHORTCUT:
   - Right-click on your desktop
   - Select "New" -> "Shortcut"
   - For location, paste: python "C:\\Users\\anngu\\Downloads\\Fruit fly ai\\desktop_app\\main_app.py"
   - Name it: "Fruit Fly AI"
   - Click Finish
   - Right-click the new shortcut -> Properties
   - Change icon: Browse to "C:\\Users\\anngu\\Downloads\\Fruit fly ai\\icon.ico"

2. START MENU SHORTCUT:
   - Press Windows Key + R
   - Type: shell:programs
   - Right-click in the folder -> New -> Shortcut
   - Use same location as above
   - Name it: "Fruit Fly AI"
   - Add icon as above

3. PIN TO TASKBAR:
   - Right-click the desktop shortcut
   - Select "Pin to taskbar"

4. SEARCHABLE:
   - Once you create the start menu shortcut, the app will be searchable
   - Press Windows key and type "Fruit Fly AI"
   - It should appear in search results

ALTERNATIVE METHOD (BATCH FILE):
--------------------------------

1. Create a batch file to launch the app:
   - Open Notepad
   - Paste this:
     @echo off
     cd "C:\\Users\\anngu\\Downloads\\Fruit fly ai"
     python desktop_app\\main_app.py
   - Save as "Fruit Fly AI.bat" on your desktop

2. Right-click the .bat file -> Create Shortcut
3. Rename shortcut to "Fruit Fly AI"
4. Add icon as described above

MACOS:
------

1. CREATE APPLICATION BUNDLE:
   - The automated script should create a .app bundle
   - Drag the .app to your Applications folder
   - It will appear in Launchpad and Spotlight search

2. DOCK SHORTCUT:
   - Once in Applications, drag to Dock

LINUX:
------

1. DESKTOP SHORTCUT:
   - The automated script creates a .desktop file
   - Right-click the .desktop file -> Allow Launching
   - It will appear in your application menu

2. PIN TO DASHBOARD:
   - Right-click the application icon -> Add to Favorites

ICON FILE:
----------

For the icon to work properly, you need a real .ico file:
1. Create or download a fly-themed icon
2. Convert to .ico format (use icoconvert.com)
3. Save as "icon.ico" in the project root
4. Replace the placeholder file I created

SEARCHABILITY:
--------------

After creating shortcuts:
- Windows: Press Windows key + type "Fruit Fly AI"
- macOS: Press Cmd + Space + type "Fruit Fly AI"  
- Linux: Press Super key + type "Fruit Fly AI"

The app should appear in search results after creating start menu/application shortcuts.
""")