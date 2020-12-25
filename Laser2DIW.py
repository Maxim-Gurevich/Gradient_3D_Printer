import math

##########################################
# user defined parameters
##########################################
flow_rate = .01  # flow rate
flow_rate_p = .1  # high-pressure prime flow rate
ratio_calib = 0  # adjusts ratio to favor A (negative) or B (positive) -255:255
prime = [['5', '5', '0'], ['200', '5', '0'],  # coordinates of high pressure prime line
         ['200', '10', '0'], ['5', '10', '0']]  # coordinates of nominal pressure prime line
prime_f = '2400'  # G1 F value for prime lines


##########################################
# initialize remaining values
##########################################
E_value = 0  # starting extrusion position
mem_line = ''
mem_X = 0
mem_Y = 0
mem_Z = 0

##########################################
# import file
##########################################
f = open(r'C:\\Users\max_g\Pictures\image.gcode', 'r')


##########################################
# define functions
##########################################
def dist(x, y, z, x2, y2, z2):  # 3d euclidean distance
    return math.sqrt((x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2)


##########################################
# add prime lines (high pressure and nominal pressure)
# make each G1 or G0 command span one line
# delete 'ON' and 'OFF'
# convert S command to E, A, and B
##########################################
for line in f:  # parses through line by line
    if ('G1 ' in line) or ('G0 ' in line):  # how to process movement commands

        X = line[line.find('X') + 1:
                 line.find(' ', line.find('X'))]
        Y = line[line.find('Y') + 1:
                 line.find(' ', line.find('Y'))]
        Z = line[line.find('Z') + 1:
                 line.find(' ', line.find('Z'))]

        if 'G' in X:
            X = mem_X
        else:
            X = float(X)
        if 'G' in Y:
            Y = mem_Y
        else:
            Y = float(Y)
        if 'G' in Z:
            Z = mem_Z
        else:
            Z = float(Z)

        distance = dist(X, Y, Z, mem_X, mem_Y, mem_Z)

        E_value += distance * flow_rate

        mem_X = float(X)
        mem_Y = float(Y)
        mem_Z = float(Z)

        if 'ON' in mem_line:  # convert S command to E A B
            S_value = min(max(int(mem_line.replace('ON S', '')) +
                              ratio_calib, 0), 255)

            AB_ratio = ' E' + str(round(E_value, 3)) + \
                       ' A' + str(round(1 - (S_value / 255), 3)) + \
                       ' B' + str(round(S_value / 255, 3))

            print(line.strip() + AB_ratio)

        elif 'OFF' in mem_line:  # pure movement (no extrusion)
            print(line.strip() + mem_line.replace('OFF', ''))

    elif 'G90' in mem_line:  # G90 appears right before the main print
        print('G1' + prime_f)
        for num in range(2):  # repeats twice, once per prime line
            n = num * 2
            print('G0 X' + prime[n][0] + ' Y' + prime[n][1] + ' Z' + prime[n][2])
            mem_X = float(prime[n][0])
            mem_Y = float(prime[n][1])
            mem_Z = float(prime[n][2])
            distance = dist(float(prime[n+1][0]), float(prime[n+1][1]),
                            float(prime[n+1][2]), mem_X, mem_Y, mem_Z)
            if num == 0:
                E_value += distance * flow_rate_p
            else:
                E_value += distance * flow_rate
            print('G1 X' + prime[n+1][0] + ' Y' + prime[n+1][1] + ' E' +
                  str(E_value) + ' A0.5 B0.5')

            if num == 0:
                E_value = 0
                print("G92 E0")

    elif ('G1' not in line) and ('OFF' not in line) and \
            ('ON' not in line) and ('G0' not in line):  # everything else
        print(line)

    mem_line = line


##########################################
# Add end code
##########################################
E_value = max(0, E_value-10)
print('G0 Z10 E' + str(round(E_value, 3)))
print('G0 X0 Y0')

##########################################
# implement extrusion delay
##########################################


##########################################
# close/save files
##########################################
f.close()
