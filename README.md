# mitotic-spindle-tool
An image analysis Python GUI application for use in Dr. Elting's lab at NCSU. 

## Build the Executable

Install pyinstaller in your local python environment, then run the following command in the directory containing the "mitotic-spindle-tool" repository. The additional arguments were included in July 2024 to circumvent issues between current versions of pyinstaller and the project's required python packages.

```shell
pyinstaller --onefile --noconsole --name=SpindleTool --collect-submodules=numpy.f2py --collect-submodules=scipy._lib.array_api_com-pat.numpy.fft --collect-submodules=scipy.special._special_ufuncs ../mitotic-spindle-tool/src/spindleGUI.py
```

The base command below can be used if compatible versions of pyinstaller and the required packages are used:

```shell
pyinstaller --onefile --noconsole --name=SpindleTool ../mitotic-spindle-tool/src/spindleGUI.py
```
