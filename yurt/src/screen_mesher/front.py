#
# create, to stdout, an obj format mesh for the main wall of the yurt
#

#
# strategy:
#     create the spec'ed curve
#     copy for floor and ceiling
#     tweak to reflect measured imperfections (not yet implemented)
#     output header, vertices, and faces
#
# spec
#    96" radius for the central portion from -65 to 65 degrees
#    center axis where back edge of screens end
#    72" radius for 33.10 degrees more
#    	 (subtending 25 degrees more at center axis)
#
# X goes right (east)
# Y goes up
# Z goes into the yurt (north
#
#
# front.obj mesh done by JNH has 3" vertical tiles about 1 or 1.5" horizontally
# wall is about 300" horizontally, 96" vertically
# calculation units are inches, taken from "curved_screens.v0.pdf"
# output units are feet
#

import math
import datetime

#
# return list of N points on designed profile curve for main wall
#

def profile(N):
    ret = []
    for i in range(-(N-1),N,2):		# step by two to account for left+right sides
    	theta = (i/(N-1.0))*90
	if (theta < -65):
	    cx = -21.751		# recenter for tighter radius
	    cz = 10.143
	    r = 72
					# scale theta for tighter radius
					# but only amount before -65
	    theta = (theta+65.0) * (33.098482/25.0) - 65.0
	elif (theta > 65):
	    cx = 21.751
	    cz = 10.143
	    r = 72
					# scale theta for tighter radius
					# but only amount past 65
	    theta = (theta-65.0) * (33.098482/25.0) + 65.0
	else:
	    cx = 0
	    cz = 0
	    r = 96
	x = cx + r*math.sin(math.radians(theta))
	z = cz + r*math.cos(math.radians(theta))
	# print i, theta, x, z
	ret.append([x,0,z])

    return ret

#
# return list of N points on straight line starting at t and ending at b
#

def line_points(t, b, N):
    ret = []
    pt = [0,0,0]
    for j in range(N):
    	a = j/(N-1.0)
	for k in range(3):
	    pt[k] = t[k] + a*(b[k]-t[k])
	ret.append(list(pt))
    return ret
    
#
# output obj file header
#

def write_obj_header(w, h):
    print "# front.py created this obj file on ", datetime.date.today().isoformat()
    print "# the mesh is %d vertices wide and %d vertices high" % (w, h)
    print "front_wall_centered"


#
# output indices of vertices for one face given horizontal
# and vertical locations of those vertices
#

def output_face(w1,h1,w2,h2,w3,h3,NH):
    i1 = w1*NH + h1 + 1
    i2 = w2*NH + h2 + 1
    i3 = w3*NH + h3 + 1
    print "f %d %d %d" % (i1,i2,i3)


################################################################

NW = 217	# number of vertices horizontally (was 200)
     		# 217 means that 65 degrees is hit exactly
NH = 33		# number of vertices vertically (was 33)

# create profile curve
p = profile(NW)

# print p

# create top and bottom at -48" and 48"
bottom = []
top = []
for pt in p:
    # print pt
    pt[1] = -48.0
    bottom.append(list(pt))
    pt[1] = 48.0
    top.append(list(pt))

# write out obj header
write_obj_header(NW, NH)

# write out obj vertices top to bottom then left to right
assert (len(top) == len(bottom))
for i in range(len(top)):
    t = top[i]
    b = bottom[i]

    # create NH vertices from top to bottom
    pts = line_points(t, b, NH)
    for pt in pts:
    	print "v %.3f %.3f %.3f" % (pt[0]/12., pt[1]/12., pt[2]/12.)

print "s off" 	      	# dunno what this is, but was in the
       	     		# original mesh file

# output (NH-1) x (NW-1) x 2 triangular faces
for w in range(NW-1):
    for h in range(NH-1):
	# face from       w,h     w,h+1
	#                 w+1,h   w+1,h+1
	output_face(w,h,w,h+1,w+1,h,NH)
	output_face(w+1,h,w,h+1,w+1,h+1,NH)



