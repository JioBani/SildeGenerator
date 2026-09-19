import pathlib,re
s=pathlib.Path("private/codex-probe-error.log").read_text()
print(re.sub(r"[A-Za-z0-9_./+=-]{80,}","[REDACTED]",s)[-6000:])
