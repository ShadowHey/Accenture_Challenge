import os

main_py_path = "backend/main.py"
with open(main_py_path, "r") as f:
    content = f.read()

old_mount = 'app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")'
new_route = '''from fastapi.responses import FileResponse

@app.get("/hospitals")
def get_hospitals_page():
    """Serve the Hospital Admin Portal"""
    return FileResponse("frontend/hospital_portal.html")

'''

if '@app.get("/hospitals")' not in content:
    content = content.replace(old_mount, new_route + old_mount)
    with open(main_py_path, "w") as f:
        f.write(content)
    print("Updated main.py successfully.")
else:
    print("Route already exists.")
