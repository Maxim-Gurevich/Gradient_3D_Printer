import math
import tkinter as tk
from tkinter import filedialog

##########################################
# user-defined parameters
##########################################
flow_rate = .01  # flow rate
flow_rate_p = .1  # high-pressure prime flow rate
ratio_calib = 0  # adjusts ratio to favor A (negative) or B (positive) -255:255
prime = [['5', '5', '0'], ['200', '5', '0'],  # high pressure prime line xyz
         ['200', '10', '0'], ['5', '10', '0']]  # nominal pressure prime line xyz
prime_f = '2400'  # G1 F value for prime lines
depressurization_extruder_distance = 10  # positive value, applied at end of print
extrusion_delay = 1  # positive value, units of extrusion distance
##########################################
# initialize remaining values
##########################################
E_value = 0  # starting extrusion position
mem_line = ''
mem_X = 0
mem_Y = 0
mem_Z = 0

##########################################
# open original file
# saveas new file
##########################################
root = tk.Tk()
root.withdraw()
open_file_path = filedialog.askopenfilename(title="Select original G-code file"
                                                  " to convert")
f = open(open_file_path, 'r')
save_file_path = filedialog.asksaveasfilename(title="SaveAs new converted G-code"
                                                    " file")
s = open(save_file_path + '.gcode', 'x+')


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

        # Update the target location
        X = line[line.find('X') + 1:
                 line.find(' ', line.find('X'))]
        Y = line[line.find('Y') + 1:
                 line.find(' ', line.find('Y'))]
        Z = line[line.find('Z') + 1:
                 line.find(' ', line.find('Z'))]

        # if there is no new info on X Y or Z data, use previous data
        # check for 'G' because one will appear if line.find is unsuccessful
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

        if 'ON' in mem_line and 'S1\n' not in mem_line:  # convert S to E A B
            distance = dist(X, Y, Z, mem_X, mem_Y, mem_Z)
            E_value += distance * flow_rate
            S_value = min(max(int(mem_line.replace('ON S', '')) +
                              ratio_calib, 0), 255)
            AB_ratio = ' E' + str(round(E_value, 3)) + \
                       ' A' + str(round(1 - (S_value / 255), 3)) + \
                       ' B' + str(round(S_value / 255, 3))
            # print(line.strip() + AB_ratio)
            s.write(line.strip() + AB_ratio + '\n')

        elif ('OFF' in mem_line) or ('S1\n' in mem_line):  # no extrusion
            # print(line.strip())
            s.write(line.strip() + '\n')

        # remember current position
        mem_X = float(X)
        mem_Y = float(Y)
        mem_Z = float(Z)

    elif 'G90' in mem_line:  # G90 appears right before the main print
        # print('G1 ' + prime_f)  # manually sets feed rate
        s.write('G1 ' + prime_f + '\n')

        for num in range(2):  # repeats twice, once per prime line
            n = num * 2
            #  get in position to start line
            # print('G0 X' + prime[n][0] + ' Y' + prime[n][1] + ' Z' + prime[n][2])
            s.write('G0 X' + prime[n][0] + ' Y' + prime[n][1] +
                    ' Z' + prime[n][2] + '\n')
            mem_X = float(prime[n][0])
            mem_Y = float(prime[n][1])
            mem_Z = float(prime[n][2])
            distance = dist(float(prime[n + 1][0]), float(prime[n + 1][1]),
                            float(prime[n + 1][2]), mem_X, mem_Y, mem_Z)

            if num == 0:  # sets a different flow rate for first prime line
                E_value += distance * flow_rate_p
            else:
                E_value += distance * flow_rate

            # extrude the line
            # print('G1 X' + prime[n + 1][0] + ' Y' + prime[n + 1][1] + ' E' +
            #       str(E_value) + ' A0.5 B0.5')
            s.write('G1 X' + prime[n + 1][0] + ' Y' + prime[n + 1][1] + ' E' +
                    str(E_value) + ' A0.5 B0.5' + '\n')

            # after the high-pressure line, the E_value needs to be reset
            # because the stepper motors have skipped steps
            if num == 0:
                E_value = 0
                # print('G92 E0')
                s.write('G92 E0' + '\n')

    elif ('G1' not in line) and ('OFF' not in line) and \
            ('ON' not in line) and ('G0' not in line):  # everything else
        # print(line)
        s.write(line.strip() + '\n')

    # the line is remembered to enable combining two lines into one
    mem_line = line

##########################################
# add end code
##########################################
E_value = max(0, E_value - depressurization_extruder_distance)
# print('G0 Z10 E' + str(round(E_value, 3)))
# print('G0 X0 Y0')
s.write('G0 Z10 E' + str(round(E_value, 3)) + '\n')
s.write('G0 X0 Y0' + '\n')

##########################################
# implement extrusion delay
##########################################
s.seek(0)  # navigate to the top of the file
G_code = list(s)  # store as list of lines for easier navigation
# s.truncate(0)  # erase the contents of the file

mem_E = 0  # initialize extrusion value
for item in G_code[0:100]:
    if ('G0' not in item) and ('G1' not in item):
        print(item.strip())
    elif 'E' in item:
        E_pos = item[item.find('E') + 1:item.find(' ', item.find('E'))]
        E_target = float(E_pos) - extrusion_delay
        if (E_target > 0) and (E_pos != mem_E):
            mem_E = E_pos
            for count, mem in enumerate(G_code[item.index():0]):
                if float(mem[mem.find('E') + 1:mem.find(' ', mem.find('E'))]) \
                        < E_target:
                    split_line_pos = item.index()-count
                    break
        #next stuff

        # find the line where that E value occurs unless it is negative
        # check lines one at a time by scrolling up the file from position
        # duplicate the command
        # change the first X Y Z to desired values
        # a tiny bit of math
        # change the ratios of all following commands (including duplicate)
    # else, just import the line

##########################################
# close/save files
##########################################
f.close()
s.close()
