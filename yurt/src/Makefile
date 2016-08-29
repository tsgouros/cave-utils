CPP = g++
CPPFLAGS = -Wall -g
LDFLAGS = 

TARGET = bandwidthTest
### These lines are for access to the VRG3D and G3D installation
### directories. All other necessary software is assumed to be
### installed in the system-wide directories.

EXTRA_INCLUDES = -I${VRG3D_BASE}/include -I/gpfs/runtime/opt/ffmpeg/0.6.1/include/
EXTRA_LIBS = -L${VRG3D_BASE}/lib  -L/gpfs/runtime/opt/ffmpeg/0.6.1/lib

OBJDIR = obj

SRCS = $(shell ls *.cpp)

OBJS = $(SRCS:%.cpp=$(OBJDIR)/%.o)

INCLUDE_DIRS = -I. $(EXTRA_INCLUDES)

LIB_DIRS = $(EXTRA_LIBS)

LIBS = -Xlinker --start-group  -Xlinker -ldl  -Xlinker -lX11 -Xlinker \
	-lXext  -Xlinker -lpthread  -Xlinker -lz  -Xlinker -ljpeg  -Xlinker \
	-lpng  -Xlinker -lzip  -Xlinker -lSDL -Xlinker -lvrg3d  -Xlinker \
	-lavutil  -Xlinker -lavformat  -Xlinker -lavcodec  -Xlinker -lGLG3D \
	-Xlinker -lG3D -Xlinker -lGLU -Xlinker -lGL -Xlinker --end-group \
	-lvrpn -lglut -lXmu -lmplEasyBlendSDK \
	-lswscale 

all: bandwidthTest

bandwidthTest: obj/bandwidthTest.o 
	$(CPP) $(LDFLAGS) -o bandwidthTest $^ $(LIB_DIRS) $(LIBS)

$(OBJDIR)/%.o: %.cpp
	mkdir -p $(OBJDIR)
	$(CPP) $(CPPFLAGS) -c $< -o $@ $(INCLUDE_DIRS)

clean:
	rm -f $(TARGET) $(OBJDIR)/*.o demo-log.txt
	rm -rf $(OBJDIR)
