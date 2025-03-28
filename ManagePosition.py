from database import *
import numpy as np


conn = get_db_connection()
curs = conn.cursor()



def generate_positions(df):
    #Prends en entrée la liste  des id des théorèmes et renvoie leur position suivant une grille
    n = len(df)
    # Distribuer les théorèmes sur une sphère
    cols = int(np.ceil(n ** (1/2)))  # Nombre de colonnes en 3D
    rows = cols
    layers = cols
    positions = []
    for i in range(len(df)):
        x = (i % cols) * 10  # Espacement sur X
        y = ((i // cols) % rows) * 10  # Espacement sur Y
        z = 0  # Espacement sur Z
        positions.append((df[i][0],x, y, z))

    return positions

curs.execute("SELECT id,x,y,z FROM concepts ORDER BY id ")
pos = curs.fetchall()
posC = generate_positions(pos)
print(posC)

for i in range(len(pos)):
    curs.execute("UPDATE concepts SET x= %s,y=%s,z=%s WHERE id = %s; ", (posC[i][1], posC[i][2], posC[i][3], posC[i][0]))

conn.commit()
curs.close()
conn.close()