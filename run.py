"""Entrada de desarrollo: un servidor que sirve API + frontend.  python run.py"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8700, reload=True)
