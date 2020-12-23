Laser2DIW parses through laser G-code and converts it to 
G-code compatible with the LulzGradient printer.

The LulzGradient printer uses the 'G1 X Y Z E A B' G-code format 
supported by Marlin firmware

Example Laser G-code:  
G1 X107.80  
ON S184  
G1 X108.10  
ON S189  
G1 X108.20  
ON S202  
G1 X108.30  
ON S220  
G1 X108.40  
ON S240  
G1 X108.50  
ON S252  
G1 X108.60  
ON S255  
G1 X109.30  
OFF  
G0 X109.30 Y10.30 F3600  
ON S255  
G1 X108.60 F2400  
ON S253  
G1 X108.50  
ON S242  
G1 X108.40  
ON S224  
G1 X108.30  
ON S205  
G1 X108.20  
ON S190  