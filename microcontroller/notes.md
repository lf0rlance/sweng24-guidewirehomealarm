# To upload files

```bash
foreach ($file in Get-ChildItem src\*.py) { mpremote connect COM3 fs cp $file.FullName ":$($file.Name)" }
```

# To run

```bash
mpremote connect COM3 exec "import main"
```

# Ctrl c to stop
