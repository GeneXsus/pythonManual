# importamos la librería
from fastapi import FastAPI


# definimos la aplicación 
app = FastAPI()



# creamos la función que devuelve un diccionario, 
# el decorador añade la funcion a la app en el endpoint /
@app.get('/')   
async def saludar():    
    return {'mensaje': 'Hola Mundo!!!!!'}