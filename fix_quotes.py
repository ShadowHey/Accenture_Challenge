with open("frontend/app.js", "r") as f:
    text = f.read()
text = text.replace('click "Update Info"', "click 'Update Info'")
with open("frontend/app.js", "w") as f:
    f.write(text)
