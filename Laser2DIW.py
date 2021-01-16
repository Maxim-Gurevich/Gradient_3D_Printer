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
extrusion_delay = .01  # positive value, units of extrusion distance
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


def extract(string, thing):  # returns string of value associated with the letter
    return string[string.find(thing) + 1:
                  string.find(' ', string.find(thing))]


##########################################
# add prime lines (high pressure and nominal pressure)
# make each G1 or G0 command span one line
# delete 'ON' and 'OFF'
# convert S command to E, A, and B
##########################################
for line in f:  # parses through line by line
    if ('G1 ' in line) or ('G0 ' in line):  # how to process movement commands

        # Update the target location
        X = extract(line, 'X')
        Y = extract(line, 'Y')
        Z = extract(line, 'Z')

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
G_code = []
past_prime = False
mem_A = .5  # initialize extrusion value
start = 0
store = []
E_pos = 0
for line in s:  # iterate line by line
    G_code.append(line)  # build up result
    if ('A' in line) and (('G0' in line) or ('G1' in line)):
        A_value = float(extract(line, 'A'))
        E_target = E_pos - extrusion_delay
        if (E_target > 0) and (A_value != mem_A):  # ratio change detected
            mem_A = A_value
            for item in G_code:
                if 'G92' in item:
                    past_prime = True
                if (('G0' in item) or ('G1' in item)) and (' A' in item) and \
                        (float(extract(item, 'E')) > E_target) and past_prime:
                    # the target line has been found and now needs to be split
                    # into two lines to sneak in an extrusion change at the
                    # proper moment
                    ind = G_code.index(item)  # determine the location of target
                    start_point = []  # start of move to be split
                    end_point = []  # end of move to be split
                    #  investigate the previous state of the printer
                    for q, i in enumerate(['X', 'Y', 'Z', 'E', 'A']):
                        found = False
                        offset = 1  # begin search with previous line
                        term = '0'
                        end_point.append(extract(G_code[ind], i))
                        # search until found
                        while (not found) and ('G' not in end_point[q]):
                            if ind - offset >= 0:
                                term = extract(G_code[ind - offset], i)
                            else:
                                term = extract(store[0 - offset + ind], i)

                            if 'G' not in term:
                                found = True
                            else:
                                offset += 1

                        start_point.append(term)
                    #  proportion of distance derived from extrusion values
                    prop = ((E_target - float(start_point[3])) /
                            (float(end_point[3]) -
                             float(start_point[3])))

                    # the following lines construct line_1 and line_2

                    # line_1 maintains the current AB ratio and
                    # stops at the point of ratio change

                    # line_2 adopts A_value and finishes the move

                    line_1 = line_2 = 'G1'  # reset the strings
                    for count, letter in enumerate([' X', ' Y', ' Z']):
                        #  only include necessary coordinate data
                        if 'G' not in end_point[count]:
                            move = round(float(start_point[count]) +
                                         ((float(end_point[count]) -
                                           float(start_point[count])) * prop), 3)
                            line_1 += letter + str(move)
                            line_2 += letter + end_point[count]

                    line_1 += ' E' + str(round(E_target, 3))
                    line_1 += ' A' + end_point[4]
                    line_1 += ' B' + str(round(1 - float(end_point[4]), 3))

                    line_2 += ' E' + end_point[3]
                    line_2 += ' A' + str(A_value)
                    line_2 += ' B' + str(round((1 - A_value), 3))

                    # change the ratios of all following commands
                    for u in range(ind, len(G_code)):
                        if 'G' not in extract(G_code[u], 'A'):
                            G_code[u] = G_code[u].replace(
                                'A' + extract(G_code[u], 'A'),
                                'A' + str(A_value))
                            G_code[u] = G_code[u].replace(
                                'B' + extract(G_code[u], 'B'),
                                'B' + str(round((1 - A_value), 3)))

                    # insert the new lines into the list
                    G_code.pop(ind)
                    G_code.insert(ind, line_1)
                    G_code.insert(ind + 1, line_2)

                    for r in range(ind):
                        store.append(G_code.pop(0).rstrip())
                    break  # exit for loop

        E_pos = float(extract(line, 'E'))
        print(E_pos)

for t in G_code:
    store.append(t.rstrip())
s.truncate(0)
s.seek(0)
for line in store:
    s.write(line.strip() + '\n')
##########################################
# close/save files
##########################################
f.close()
s.close()
