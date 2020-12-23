import math

##########################################
# Initialization and user defined parameters
##########################################
flow_rate = .01  # flow rate
E_value = 0  # starting extrusion position
mem_line = ""
mem_X = 0
mem_Y = 0
mem_Z = 0

##########################################
# import file
##########################################
f = open(r"C:\\Users\max_g\Pictures\image.gcode", "r")

##########################################
# Add prime lines (high pressure and nominal pressure)
##########################################


##########################################
# make each G1 or G0 command span one line
# delete "ON" and "OFF"
# convert S command to E, A, and B
##########################################
for line in f:
    if ("G1 " in line) or ("G0 " in line):

        X = line[line.find("X") + 1:
                 line.find(" ", line.find("X"))]
        Y = line[line.find("Y") + 1:
                 line.find(" ", line.find("Y"))]
        Z = line[line.find("Z") + 1:
                 line.find(" ", line.find("Z"))]

        if "G" in X:
            X = mem_X
        else:
            X = float(X)
        if "G" in Y:
            Y = mem_Y
        else:
            Y = float(Y)
        if "G" in Z:
            Z = mem_Z
        else:
            Z = float(Z)

        dist = math.sqrt((X - mem_X) ** 2 + (Y - mem_Y) ** 2 +
                         (Z - mem_Z) ** 2)

        E_value += dist * flow_rate

        mem_X = float(X)
        mem_Y = float(Y)
        mem_Z = float(Z)

        if "ON" in mem_line:
            S_value = int(mem_line.replace("ON S", ""))

            AB_ratio = " E" + str(round(E_value, 3)) + \
                       " A" + str(round(1 - (S_value / 255), 3)) + \
                       " B" + str(round(S_value / 255, 3))

            print(line.strip() + AB_ratio)

        elif "OFF" in mem_line:
            print(line.strip() + mem_line.replace("OFF", ""))

    elif ("G1" not in line) and ("OFF" not in line) and \
            ("ON" not in line) and ("G0" not in line):
        print(line)

    mem_line = line

##########################################
# Add end code
##########################################


##########################################
# implement extrusion delay
##########################################


##########################################
# close/save files
##########################################
f.close()
