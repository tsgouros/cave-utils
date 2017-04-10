#!/gpfs/runtime/opt/python/2.7.3/bin/python
#!/opt/local/bin/python
#!/usr/bin/python


# TODO
#   handle eco mode


import curses
import time
import os
from threading import Thread


# class for projector objects
#	up, down, right, left index to neighbor projectors
#	y, x give screen coords of red
#	r, g, b projector gains
class proj :
    pass

p = [proj() for i in range(69)]

# unchanging labels on display
labels = {(0,18,"#00#01      Ceiling"),
          (1,17,"R"), (2,17,"G"), (3,17,"B"),
          (5,3,"#10#12    Top Wall"),
          (5,48,"#38#40  Top Doors"),
          (10,3,"#11#13    Bottom Wall"),
          (10,48,"#39   Bottom Doors"),
          (15,18,"#50 R  G  B     Floor"),
          (1,17,"R"), (2,17,"G"), (3,17,"B"),
          (6,2,"R"), (7,2,"G"), (8,2,"B"),
          (11,2,"R"), (12,2,"G"), (13,2,"B"),
          }

def out_labels(stdscr) :
    for t in labels:
        stdscr.addstr(t[0], t[1], t[2])
    curses.doupdate()
    
def gain_str(g) :
    assert g > 0 and g < 200
    ret = "00"
    o = str(g % 10)             # ones digit
    t = int(g / 10)
    if ( t == 0) :
        ret = '0' + o
    elif (t < 10) :
        ret = str(t) + o
    else :
        ret = chr(ord('A') + t - 10) + o
    assert len(ret) == 2
    return ret

def out_gain(stdscr, n) :
    y0 = y1 = y2 = p[n].y
    x0 = x1 = x2 = p[n].x
    if (n<50) :
        y1 = y0 + 1
        y2 = y0 + 2
    else :
        x1 = x0 + 3
        x2 = x0 + 6
    stdscr.addstr(y0, x0, gain_str(p[n].r))
    stdscr.addstr(y1, x1, gain_str(p[n].g))
    stdscr.addstr(y2, x2, gain_str(p[n].b))

def eco_str(e) :
    assert g > 0 and g < 200
    if e == "eco":
        return "*"
    elif e == "std" or e == "unset":
        return " "
    assert 0

def out_eco(stdscr, n) :
    y = p[n].y
    if (n<50) :
        x = p[n].x + 2
    else :
        x = p[n].x + 8
    stdscr.addstr(y, x, eco_str(p[n].eco))


def out_gains(stdscr) :
    for i in range(69) :
        out_gain(stdscr, i)

"""   screen layout

              111111111122222222223333333333444444444455555555556666666
    0123456789012345678901234567890123456789012345678901234567890123456

00                      #00#01      Ceiling
01                     R 95 95 95 95 95 95 95 95 95 95
02                     G 95 95 95 95 95 95 95 95 95 95
03                     B 95 95 95 95 95 95 95 95 95 95
04
05     #10#12    Top Wall			    #38#40  Top Doors
06    R 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
07    G 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
08    B 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
09
10     #11#13    Bottom Wall                        #39   Bottom Doors
11    R 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
12    G 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
13    B 95 95 95 95 95 95 95 95 95 95 95 95 95 95    95 95 95 95 95 95
14
15                  #50 R  G  B     Floor
16                     95 95 95    95 95 95    95 95 95
17               95 95 95    95 95 95    95 95 95    95 95 95
18               95 95 95    95 95 95    95 95 95    95 95 95
19         95 95 95    95 95 95    95 95 95    95 95 95    95 95 95
20                     95 95 95    95 95 95    95 95 95


"""


def init_gain_coords() :
    coord_string = """00 01 19
01 01 22
02 01 25
03 01 28
04 01 31
05 01 34
06 01 37
07 01 40
08 01 43
09 01 46
10 06 04
11 11 04
12 06 07
13 11 07
14 06 10
15 11 10
16 06 13
17 11 13
18 06 16
19 11 16
20 06 19
21 11 19
22 06 22
23 11 22
24 06 25
25 11 25
26 06 28
27 11 28
28 06 31
29 11 31
30 06 34
31 11 34
32 06 37
33 11 37
34 06 40
35 11 40
36 06 43
37 11 43
38 06 49
39 11 49
40 06 52
41 11 52
42 06 55
43 11 55
44 06 58
45 11 58
46 06 61
47 11 61
48 06 64
49 11 64
50 16 19
51 16 31
52 16 43
53 17 13
54 17 25
55 17 37
56 17 49
57 18 13
58 18 25
59 18 37
60 18 49
61 19 07 
62 19 19
63 19 31 
64 19 43 
65 19 55 
66 20 19
67 20 31
68 20 43"""
    i = 0
    for line in coord_string.split('\n') :
        t = line.split()
        assert len(t) == 3, "y,x string error"
        assert int(t[0]) == i, "y,x coord setting mismatch"
        i = i + 1
        p[int(t[0])].y = int(t[1])
        p[int(t[0])].x = int(t[2])
        
def updown(below, above):
    p[below].up = above
    p[above].down = below

def rightleft(left, right):
    p[left].right = right
    p[right].left = left

def floorrow(l, r, d):
    for i in range(l,r):
        rightleft(i,i+1)
        if (d > 0) :
            updown(min(68,i+d),i)

def init_pdirs():
    # first set all directions to be no-ops to avoid crashes
    for i in range(69):
        p[i].down = i
        p[i].up = i
        p[i].right = i
        p[i].left = i
    # set ceiling top no-ops first to avoid overwriting
    p[0].left = 0
    p[9].right = 9
    # up from top wall    
    updown(10, 0)                   
    updown(12, 1)
    updown(14, 1)
    updown(16, 2)
    updown(18, 3)
    updown(20, 3)
    updown(22, 4)
    updown(24, 5)
    updown(26, 6)
    updown(28, 6)
    updown(30, 7)
    updown(32, 8)
    updown(34, 8)
    updown(36, 9)
    for i in range(0,9):
        # right on ceiling
        rightleft(i,i+1)
    for i in range(11,50,2):
        # up from bottom wall and bottom doors
        updown(i, i-1)
        # right from walls and doors
        r = i+2
        if r >=50 :
            r -= 40
        rightleft(i, r)
        rightleft(i-1,r-1)
    # floor/wall
    updown(61 ,11)
    updown(57 ,13)
    updown(53 ,15)
    updown(53 ,17)
    updown(50 ,19)
    updown(50 ,21)
    updown(51 ,23)
    updown(51 ,25)
    updown(52 ,27)
    updown(52 ,29)
    updown(56 ,31)
    updown(56 ,33)
    updown(60 ,35)
    updown(65 ,37)
    updown(66 ,39)
    updown(66 ,41)
    updown(67 ,43)
    updown(67 ,45)
    updown(68 ,47)
    updown(68 ,49)
    # floor rows
    floorrow(50,52,3)
    floorrow(53,56,4)
    updown(56,52)
    floorrow(57,60,4)
    floorrow(61,65,5)
    updown(65,60)
    floorrow(66,68,-1)

def read_config() :
    f = open('yurtcol.config', 'r')
    for i in range(69):
        l = f.readline()
        t = l.split()
        assert len(t) == 4 or len(t) == 5, "config file error -- line with other than 4 or 5 toks"
        assert int(t[0]) == i, "mismatched projector index"
        p[int(t[0])].r = int(t[1])
        p[int(t[0])].g = int(t[2])
        p[int(t[0])].b = int(t[3])
        p[int(t[0])].pr = -1        # set value in projector
        p[int(t[0])].pg = -1        # set value in projector
        p[int(t[0])].pb = -1        # set value in projector
        p[int(t[0])].eco = "unset"  # dummy if config not set
        p[int(t[0])].peco = "unset" # set value in projector
        if len(t) == 5:
            assert t[4] == "eco" or t[4] == "std"
            p[int(t[0])].eco = t[4]
    f.close()

def write_config() :
    f = open('yurtcol.config', 'w')
    for i in range(69):
        line = str(i) + "  " + str(p[i].r) + " " + str(p[i].g) + " " + str(p[i].b)
        if (p[i].eco == "eco" or p[i].eco == "std"):
            line = line + " " + p[i].eco
        line = line + "\n"
        f.write(line)
    f.close()

def do_curses(stdscr) :
    init_pdirs()
    out_labels(stdscr)
    out_gains(stdscr)
    done = 0
    curproj = 22
    while (not done) :
        c = stdscr.getch()
        if (c == ord('q')) :
            done = 1
        elif (c == ord('j')) :
            # move "down" one projector
            curproj = p[curproj].down
        elif (c == ord('k')) :
            # move "down" one projector
            curproj = p[curproj].up
        elif (c == ord('h')) :
            # move "left" one projector
            curproj = p[curproj].left
        elif (c == ord('l')) :
            # move "right" one projector
            curproj = p[curproj].right
        elif (c == ord('_') or c == ord('-')) :
            # decrease all three gains by one
            p[curproj].r = max(1,p[curproj].r - 1)
            p[curproj].g = max(1,p[curproj].g - 1)
            p[curproj].b = max(1,p[curproj].b - 1)
            out_gain(stdscr, curproj)
        elif (c == ord('+') or c == ord('=')) :
            # increase all three gains by one
            p[curproj].r = min(199,p[curproj].r + 1)
            p[curproj].g = min(199,p[curproj].g + 1)
            p[curproj].b = min(199,p[curproj].b + 1)
            out_gain(stdscr, curproj)
        elif (c == ord('r')) :
            # decrease red
            p[curproj].r = max(1,p[curproj].r - 1)
            out_gain(stdscr, curproj)
        elif (c == ord('R')) :
            # increase red
            p[curproj].r = min(199,p[curproj].r + 1)
            out_gain(stdscr, curproj)
        elif (c == ord('g')) :
            # decrease green
            p[curproj].g = max(1,p[curproj].g - 1)
            out_gain(stdscr, curproj)
        elif (c == ord('G')) :
            # increase green
            p[curproj].g = min(199,p[curproj].g + 1)
            out_gain(stdscr, curproj)
        elif (c == ord('b')) :
            # decrease blue
            p[curproj].b = max(1,p[curproj].b - 1)
            out_gain(stdscr, curproj)
        elif (c == ord('B')) :
            # increase blue
            p[curproj].b = min(199,p[curproj].b + 1)
            out_gain(stdscr, curproj)
        elif (c == ord('e')) :
            p[curproj].eco = "eco"
            out_eco(stdscr, curproj)
        elif (c == ord('s')) :
            p[curproj].eco = "std"
            out_eco(stdscr, curproj)

        stdscr.addstr(0,0,str(curproj))
        stdscr.addstr(p[curproj].y, p[curproj].x, "")


#
# code that figures out what projectors need to be updated,
# constructs commands to do that updating, and executes them
# in a separate thread
#

def find_all_red(val, start) :
    ret = str(start)
    for i in range(start+1, 69) :
        if (p[i].pr != p[i].r and p[i].r == val) :
            ret = ret + "," + str(i)
    return ret

def find_all_green(val, start) :
    ret = str(start)
    for i in range(start+1, 69) :
        if (p[i].pg != p[i].g and p[i].g == val) :
            ret = ret + "," + str(i)
    return ret

def find_all_blue(val, start) :
    ret = str(start)
    for i in range(start+1, 69) :
        if (p[i].pb != p[i].b and p[i].b == val) :
            ret = ret + "," + str(i)
    return ret

def find_all_eco(val, start) :
    ret = str(start)
    for i in range(start+1, 69) :
        if (p[i].peco != p[i].eco and p[i].eco == val) :
            ret = ret + "," + str(i)
    return ret

def build_command(plist, var, val) :
    return "./dhl_pjcontrol " + plist + " raw " + var + " = " + str(val)

def build_command_eco(plist, val) :
    return "./dhl_pjcontrol " + plist + " " + str(val)

def next_command() :
    for i in range(69) :
        # find first needed change
        if (p[i].eco != p[i].peco):
            projectors = find_all_eco(p[i].eco, i)
            cmd = build_command_eco(projectors, p[i].eco)
            for n in projectors.split(',') :
                p[int(n)].peco = p[int(n)].eco
            return cmd
        val = p[i].r
        if p[i].pr != val :
            projectors = find_all_red(val, i)
            cmd = build_command(projectors, "red.gain", val)
            for n in projectors.split(',') :
                p[int(n)].pr = val
            return cmd
        val = p[i].g
        if p[i].pg != val :
            projectors = find_all_green(val, i)
            cmd = build_command(projectors, "green.gain", val)
            for n in projectors.split(',') :
                p[int(n)].pg = val
            return cmd
        val = p[i].b
        if p[i].pb != val :
            projectors = find_all_blue(val, i)
            cmd = build_command(projectors, "blue.gain", val)
            for n in projectors.split(',') :
                p[int(n)].pb = val
            return cmd

def threaded_function():
    # keep the projector settings matching the interactive input
    i = 0
    while (1) :
        if not p[0].alive :
            return
        cmd = next_command()
        if (cmd) :
            os.system(cmd)
        else :
            time.sleep(1)

if __name__ == "__main__":
    print "thread finished...exiting"


print "hello world\n"
read_config()
init_gain_coords()
time.sleep(1)
p[0].alive = 1
thread = Thread(target = threaded_function, args = ())
thread.start()
curses.wrapper(do_curses)
p[0].alive = 0
thread.join()
write_config()
print "goodbye world\n"
