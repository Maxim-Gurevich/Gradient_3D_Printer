import math
import tkinter as tk
from tkinter import filedialog

##########################################
# user-defined parameters
##########################################
extrusion_delay = .01  # positive value, units of extrusion distance

##########################################
# initialize remaining values
##########################################
E_value = 0  # starting extrusion position

##########################################
# open original file
# saveas new file
##########################################
# set up tkinter, the GUI python module
root = tk.Tk()
root.withdraw()
# get input from user about what file to open
open_file_path = filedialog.askopenfilename(title="Select original G-code file"
                                                  " to delay")
f = open(open_file_path, 'r')  # open the file
# get input about save location and
save_file_path = filedialog.asksaveasfilename(title="SaveAs new delayed G-code"
                                                    " file")
# create a new file, adding '.gcode' at the end
s = open(save_file_path + '.gcode', 'x+')


##########################################
# define functions
##########################################
#  this function is used extensively to read G-code
def extract(string, thing):  # returns string of value associated with the letter
    #  the characters immediately after the 'thing' are returned
    return string[string.find(thing) + 1:
                  string.find(' ', string.find(thing))]


##########################################
# implement extrusion delay
##########################################
G_code = []
past_prime = False
mem_A = .5  # initialize extrusion value
store = []
E_pos = 0
for line in f:  # iterate line by line
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

for line in store:
    s.write(line.strip() + '\n')
##########################################
# close/save files
##########################################
f.close()
s.close()
