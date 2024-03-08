For anyone reading this, may God save your soul because using buildozer is a living hell.
1. install buildozer as in the documentation at https://buildozer.readthedocs.io/en/latest/installation.html targeting android.
2. install gettext, this is needed for buildozer but isn't automatically installed. The command is sudo apt install -y gettext
3. get the camerax provider from github for camera4kivy using command: git clone https://github.com/Android-for-Python/camerax_provider.git followed by rm -rf camera_provider/.git
4. set up the buildozer.spec file, this file can be obtained by running the command buildozer init, take care to not specify the version of python or kivy in the requirements
5. for debugging, install the android sdk on the winsows system, using powershell navigate to the platform-tools folder. Then start a server using command .\adb tcpip 5555 and check if your connected phone is found using .\adb devices. The phone must be set in develloper mode and has to give the pc the required permissions. Next in the ubuntu os navigate to the platform-tools folder, connect using the command .\adb connect ***local ip adress phone*** and check connection using .\adb devices.
6. every time the buildozer. spec file is changed, the command buildozer appclean must be run.
7. to create an apk file, run the command buildozer -v android debug.
8. to debug this file, with a connected phone, run command buildozer -v android deploy run logcat | grep python
9. pray

in the buildozer.spec file take care to
1. add all requirements for the project including python3, pil, sh, colorama and gestures4kivy
2. add all necessary file extensions in the include_exts
3. add all needed permissions
4. set the android api to 33
5. set the min api to 28
6. set accept sdk license tot True
7. set the archs to just arm64-v8a
8. set the p4a hook to the gradle_options.py in the camerax_provider folder

Failing to do any of these may lead to hours of debugging

good luck