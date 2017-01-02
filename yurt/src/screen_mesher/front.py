#
# create, to stdout, an obj format mesh for the main wall of the yurt
#

#
# strategy:
#     create the spec'ed curve
#     copy for floor and ceiling
#     tweak to reflect measured imperfections (not yet implemented)
#     output header, vertices, and faces
#     output comment with 3D control points
#
#    spec
#        96" radius for the central portion from -65 to 65 degrees
#        center axis where back edge of screens end
#        72" radius for 33.10 degrees more on each side
#    	     (subtending 25 degrees more at center axis)
#    in revised version, measurements of distance from 0,0 point
#	 taken every 10 degrees and interpolated to get main curve
#        with any slight variations top and bottom and at the ends
#    tweaked in (north) from the screen ends
#
# X goes right (east)
# Y goes down
# Z goes into the yurt (north)
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

def profile(N, is_top):
    ret = []
    for i in range(-(N-1),N,2):		# step by two to account for left+right sides
    	theta = (i/(N-1.0))*90


	# now do a really crude adjustment to the angle range to adjust for
	# differences top, bottom, right, left
	#
	#   on the top east end, the screen ends at +3/16"
	#   on the bottom east end, the screen ends at +7/16"
	#   on the top west end, the screen ends at +3/4"
	#   on the bottom west end, the screen ends at +1/16"
	#
	# also set the correct radius

	if (is_top):
	    if (theta > 0):
	        # top east wall ends 3/16" short, which this corrects for
	        theta = theta * (90.-math.degrees(math.atan2(3/16.0, 93)))/90.
	    else:
	        # top west wall ends 3/4" short, which this corrects for
	        theta = theta * (90.-math.degrees(math.atan2(3/4.0, 93)))/90.
        else:
	    if (theta > 0):
	        # bottom east wall ends 7/16 short, which this corrects for
	        theta = theta * (90.-math.degrees(math.atan2(7/16.0, 93)))/90.
	    else:
	        # bottom east wall ends 1/16 short, which this corrects for
	        theta = theta * (90.-math.degrees(math.atan2(1/16.0, 93)))/90.

	(t_r, b_r) = lookup_wall_radius(theta)
	if (is_top):
	    r = t_r
	    y = -48.0
    	else:
	    r = b_r
	    y = 48.0

	x = r*math.sin(math.radians(theta))
	z = r*math.cos(math.radians(theta))
	ret.append([x,y,z])

    return ret

#
#  profile from specification
#

def spec_profile(N):
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

def save_profile(fname, profile):
    f = open(fname, "w")
    for pt in profile:
        f.write("%.4f %.4f\n" % (pt[0], pt[2]))
    f.close()

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
    print "o front_wall_centered"


#
# output indices of vertices for one face given horizontal
# and vertical locations of those vertices
#

def output_face(w1,h1,w2,h2,w3,h3,NH):
    i1 = w1*NH + h1 + 1
    i2 = w2*NH + h2 + 1
    i3 = w3*NH + h3 + 1
    print "f %d %d %d" % (i1,i2,i3)


#
# measurements for front wall taken with giant protractor and
# laser measurer.  The bottom edge is in feet, measured by degrees
# centered at zero and going from -90 to 90.
#
# the top edge is more complex.  It is the distance measure from
# the floor center to the top of the wall minus 0.5', which is the
# length of the adapter to the measurement device.  So it must
# be recalculated to be the right length and then corrected for
# the 8' rise to the wall/ceiling boundary
#

wall_r_data = """\
-90 7.755 10.625
-80 7.900 10.740
-70 7.980 10.815
-60 8.000 10.815
-50 8.000 10.815
-40 8.000 10.815
-30 8.000 10.815
-20 8.005 10.815
-10 8.005 10.815
  0 8.005 10.815
 10 8.010 10.815
 20 8.010 10.815
 30 8.005 10.815
 40 8.000 10.815
 50 8.005 10.825
 60 8.005 10.825
 70 8.000 10.780
 80 7.910 10.750
 90 7.750 10.630
"""

#
# measurements of diameter roughly measured from the far edge of the front screen.
# each measurement is short 6" or 0.5' because of threaded adapter
#
# 0"	15.010
# 1.5"	15.010
# 7"	15.035
# 14"	15.055
# 17"	15.035
#


wall_thetas = []
wall_bot_rs = []
wall_mid_rs = []
wall_top_rs = []

def init_wall_radii():
    i = 0
    for t in range(-90,91,10):
    	lines = wall_r_data.split("\n")
	(theta, bot, top) = lines[i].split()
	theta = float(theta)
	assert(theta == t)
	# convert bot straight to inches
	bot = float(bot) * 12.0

	# convert top to horizontal inches
	top = (float(top) + 0.5)	
	h = 8.	    		# assume measured right at ceiling
	top = 12.0*math.sqrt(top*top - h*h)

        # initialize middle as midpoint
        mid = (top + bot)/2.0
               
	wall_thetas.append(theta)
	wall_bot_rs.append(bot)
	wall_mid_rs.append(mid)
	wall_top_rs.append(top)
	i = i+1	

def lookup_wall_radius(theta):
    assert (theta >= -90 and theta <= 90)
    for i in range(len(wall_thetas) - 1):
        if (theta >= wall_thetas[i] and theta <= wall_thetas[i+1]):
	    # linearly interpolate and return the radius
    	    dt = wall_thetas[i+1] - wall_thetas[i]
	    w0 = (wall_thetas[i+1] - theta) / dt
	    w1 = (theta - wall_thetas[i]) / dt
	    assert((w1+w0) >= .999 and (w1+w0) <= 1.001)
	    bot_r = w0*wall_bot_rs[i] + w1*wall_bot_rs[i+1]
	    top_r = w0*wall_top_rs[i] + w1*wall_top_rs[i+1]
	    return (top_r, bot_r)
    assert(0)			# fell through -- bad theta




wall_mid_chords = [0, 15.010+0.5, 	# inches from edge, chord
                   1.5, 15.010+0.5, 	# added 0.5 for laser measurer
                   7., 15.035+0.5,      # extension
                   14., 15.055+0.5,
                   17., 15.035+0.5]

def init_bumps():
    for i in range(0, len(wall_mid_chords), 2):
        print wall_mid_chords[i], wall_mid_chords[i+1], wall_mid_chords[i+1]*12.0/2.0, "measured C/2"
        
        # estimate how far from end of wall in degrees
	theta = math.degrees(math.atan2(wall_mid_chords[i]/2, 93))
        print theta
        (t,b) = lookup_wall_radius(90.-theta)
	r_perf = (t+b)/2
        c_perf = r_perf*math.sin(math.radians(90.-theta))
        print r_perf, c_perf, "no-bulge expected C/2"
        print t, t*math.sin(math.radians(90.-theta)), "no-bulge top"
        print b, b*math.sin(math.radians(90.-theta)), "no-bulge bottom"


def vertex_in_comment(v):
    print "# %.4f %.4f %.4f" % (v[0]/12., v[1]/12., v[2]/12.)

################################################################

NW = 217	# number of vertices horizontally (was 200)
     		# 217 means that 65 degrees is hit exactly
NH = 33		# number of vertices vertically (was 33)

init_wall_radii()
init_bumps()

# create top profile curve
p = profile(NW, 1)	# is_top
save_profile("top.gp", p)
spec = spec_profile(NW)
save_profile("spec.gp", spec)

# create top at -48" and 48"
top = []
for pt in p:
    # print pt
    top.append(list(pt))

# create bottom profile curve
p = profile(NW, 0 )	# not is_top
save_profile("bottom.gp", p)
# create bottom at 48"
bottom = []
for pt in p:
    # print pt
    bottom.append(list(pt))

# write out obj header
write_obj_header(NW, NH)

# add comments with six control points, 3 top and 3 bottom
vertex_in_comment(top[0])
vertex_in_comment(top[(NW-1)/2])
vertex_in_comment(top[NW-1])
vertex_in_comment(bottom[0])
vertex_in_comment(bottom[(NW-1)/2])
vertex_in_comment(bottom[NW-1])

# write out obj vertices top to bottom then left to right
assert (len(top) == len(bottom))
for i in range(len(top)):
    t = top[i]
    b = bottom[i]

    # create NH vertices from top to bottom
    pts = line_points(t, b, NH)
    for pt in pts:
    	print "v %.4f %.4f %.4f" % (pt[0]/12., pt[1]/12., pt[2]/12.)

print "s off" 	      	# dunno what this is, but was in the
       	     		# original mesh file

# output (NH-1) x (NW-1) x 2 triangular faces
for w in range(NW-1):
    for h in range(NH-1):
	# face from       w,h     w+1,h
	#                 w,h+1   w+1,h+1
	# (should be counter clockwise now?)
	output_face(w,h,    w,h+1,   w+1,h,    NH)
	output_face(w+1,h,  w,h+1,   w+1,h+1,  NH)

# output commented control points at upper left, upper center, upper right
#                                    lower left, lower center, lower right

