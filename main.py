import serial, time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random

Vin = 5
Vres = 19.607*10**-3
Res = 10*10**3
E1 = 2.5
b = 2*10**3

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    hw_sensor = None
    try:
        hw_sensor = serial.Serial("COM3")
    except Exception as ex:
        print(ex)
        if hw_sensor:
            hw_sensor.close()
        await websocket.send_json({ "status": -1, "message": "Ha ocurrido un error al crear la conexion serial", "error": str(ex) })
    while True:
        hw_sensor.write('getValue'.encode('utf-8'))
        time.sleep(1)
        try:
            raw_string_b = hw_sensor.readline()
            raw_string_s = raw_string_b.decode('utf-8').replace("\n", "")
            decimal_value = int(raw_string_s, 2)
            v_analogico = round( decimal_value * Vres , 2)
            v_sus = round(v_analogico / 2, 2) 
            E2 = round(E1 - v_sus, 2) 
            delta_r = round(((E2 * 2 * Res) - (Vin * Res)) / ( E2 - Vin ), 2)
            r_sen = round(Res - delta_r , 2)
            distancia = round(r_sen / b, 2)
            
            #elif distancia >= 4.8:
            #    distancia = 5
            distancia = round(distancia, 2)
            await websocket.send_json({ 
                "status": 1, 
                "distancia": distancia, 
                "r_sen": r_sen, 
                "delta_r": delta_r, 
                "E2": E2, 
                "v_sus": v_sus, 
                "v_analogico":v_analogico,
                "binario": raw_string_s,
                "decimal": decimal_value
            })
        except Exception as ex:
            print("Error al obtener los datos: {}".format(ex))
            await websocket.send_json({ "status": 0, "data": "" })
            hw_sensor.close()
    

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)