/*
 * \author Alex Hills
 *
 * \file  gari_demo.cpp
 *
 * Adapted from chess_demo.cpp.
 */


#include <vrg3d/VRG3D.h>
#include <GL/glut.h>
#include <unistd.h>
#include <iostream>     // std::cout
#include <fstream>      // std::ifstream
#include <sys/time.h>
#include <typeinfo>
#include <queue>
//#include <chrono>
//#include <ctime>

using namespace G3D;

/** This is a sample VR application using the VRG3D library.  Two key
    methods are filled in here: doGraphics() and doUserInput().  The
    code in these methods demonstrates how to draw graphics and
    respond to input from the mouse, the keyboard, 6D trackers, and VR
    wand buttons.
*/

class MyVRApp : public VRApp
{
public:
	MyVRApp(const std::string &mySetup, char *fname) : VRApp()
	{
		// initialize the VRApp
		Log  *demoLog = new Log("demo-log.txt");

		//get Xdisplay values (0:0, 0:1 etc)
		display_name = getenv("DISPLAY");
		//get hostname (cave001, cave002 etc)
		gethostname(hostname, sizeof hostname);
		//convert hostname into string
		string hostname_string(hostname);
		//print out time before initialization
		print_time(hostname_string, "event", "preinit", "");
		// init the app -> refer to VRApp.h in VRG3D
		init(mySetup, demoLog);
		//print out time after initialization
		print_time(hostname_string, "event", "postinit", "");
		//cout << fname << endl;
		//cout << mySetup << endl;
		// The default starting point has the eye level with the chess
		// board, which is confusing for the viewer on startup, and
		// renders poorly too. Let's move the virtual space up a few units
		// for a more sensible view.
		//_virtualToRoomSpace = CoordinateFrame();

		// This is the background -- the color that appears where there is
		// nothing to render, and we'll use a nice soothing blue.
		_clearColor = Color3(0.0, 0.0, 0.0);
		// The actual models of the chess pieces are pretty messy, so they
		// are confined to another code file for the sake of tidiness.

		filename = (char*) malloc(strlen(fname) + 1);
		strcpy(filename, fname);

		id = atoi(&hostname[4]);

		loadFull = false;
		loadPart = false;
		loadEvent = false;
	}

	virtual ~MyVRApp() {}

	// getting tracking glass event name
	// currently only recording head tracker events
	// comment out necessary lines for tracking other events
	void doUserInput(Array<VRG3D::EventRef> &events)
	{
		static double joystick_x = 0.0;
		static double joystick_y = 0.0;

		for (int i = 0; i < events.size(); i++) {

			if (events[i]->getName() == "Wand_Joystick_X") {
				joystick_x = events[i]->get1DData();
			}


			else if (events[i]->getName() == "Wand_Joystick_Y") {
				joystick_y = events[i]->get1DData();
			}

			// wand button 1
			else if (events[i]->getName() == "Wand_Left_Btn_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}
			// wand button 2
			else if (events[i]->getName() == "Wand_Right_Btn_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			} 
			// wand up button
			else if (events[i]->getName() == "B03_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}
			// wand down button
			else if (events[i]->getName() == "B04_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}
			// wand left button
			else if (events[i]->getName() == "B05_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}
			// wand right button
			else if (events[i]->getName() == "B06_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			// mouse up button
			else if (events[i]->getName() == "B09_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			// mouse down button
			else if (events[i]->getName() == "B10_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			// mouse left button
			else if (events[i]->getName() == "B11_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			// mouse right button
			else if (events[i]->getName() == "B12_up") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			else if (events[i]->getName() == "Wand_Tracker") {
				//loadEvent = true;
				//event_name = events[i]->getName();
				continue;
			}

			else if (events[i]->getName() == "Head_Tracker") {
				loadEvent = true;
				event_name = events[i]->getName();
				//continue;
			}

			else if (events[i]->getName().find('aimo') != std::string::npos){
				continue;
			}


			else if (events[i]->getName() == "SynchedTime") {  
			    continue;
      		}
			else {
				// much if you are getting several tracker updates per frame.
				// getting aimo_13, 14, 15 etc
			}
				// Uncomment this to see everything..
				// This will print out the names of all events, but can be too
				cout << events[i]->getName() << endl;


			// Rotate
			// hypothetically loadPart tests for cached events
			// and loadFull tests for non-cached events
			if (fabs(joystick_x) > 0.5) {
				loadPart = true;
			}
			if (fabs(joystick_y) > 0.5 ) {
				loadFull = true;
			}
		}
	}

#define CLIENT_SLEEP 0.0005

	void doGraphics(RenderDevice *rd, bool left_eye)
	{
		// The tracker frames above are drawn with the object to world
		// matrix set to the identity because tracking data comes into the
		// system in tfilenamehe Room Space coordinate system.  Room Space is tied
		// to the dimensions of the room and the projection screen within
		// the room, thus it never changes as your program runs.  However,
		// it is often convenient to move objects around in a virtual
		// space that can change relative to the screen.  For these
		// objects, we put a virtual to ../../geoviewer/src/geoviewer_yurt.cpp
		// matrix stack before drawing them, as is done here..
		//
		rd->disableLighting();
		rd->pushState();
		//rd->setObjectToWorldMatrix(_virtualToRoomSpace);
		string hostname_string(hostname);

		// record event time 
		if (loadEvent) {
			print_time(hostname_string, "event", event_name, "");
			loadEvent = false;
		}

		// record cached reading time, adapted from bandwidthTest.cpp at /users/cavedemo/demos/BandwidthTest/src
		else if (loadPart){
			print_time(hostname_string, "cached-preload", filename, "");

			int division = 100;
      		streampos size;
      		char * memblock;
      
      		ifstream file (filename, ios::in | ios::binary | ios::ate);

      		if (file.is_open()){
      			size = file.tellg();
        		int newSize = size / division;
       			memblock = new char [newSize];
       			file.seekg (newSize * id, ios::beg);
       			file.read (memblock, newSize);
       			file.close();

       			double sizeMB = ((double) newSize) / 1024.0 / 1024.0;
       			// convert sizeMB into string for print
       			ostringstream strs;
       			strs << sizeMB;
       			string str_sizeMB;
				str_sizeMB = strs.str();
      		
      			print_time(hostname_string, "cached-postload", filename, str_sizeMB);
      			delete[] memblock;
      		}
      		loadPart = false;
		}

		// record non-cached reading time, adapted from bandwidthTest.cpp at /users/cavedemo/demos/BandwidthTest/src
		else if (loadFull){
			print_time(hostname_string, "noncached-preload", filename, "");
			streampos size;
      		char * memblock;
      		ifstream file (filename, ios::in | ios::binary | ios::ate);

      		// start reading the file
      		if (file.is_open()){
        		size = file.tellg();
        		int newSize = size;
        		memblock = new char [newSize];
        		file.seekg (0, ios::beg);
        		file.read (memblock, newSize);
        		file.close();
        		// calculate the size of the input file
        		double sizeMB = ((double) newSize) / 1024.0 / 1024.0;
        		// convert sizeMB into string for print
       			ostringstream strs;
       			strs << sizeMB;
       			string str_sizeMB;
				str_sizeMB = strs.str();
      		
      			print_time(hostname_string, "noncached-postload", filename, str_sizeMB);
      			delete[] memblock;
				}
		loadFull = false;
		}
		rd->popState();
	}


// record current time, event type and event name to -evlog.txt for specified cave node
virtual void print_time (string hostname_string, string event_type, string name, string sizeMB){
	struct timeval tv;
	struct tm * timeinfo;
	time_t rawtime;
	string output_file;

	output_file = "/tmp/" + hostname_string + "-evlog.txt";

	gettimeofday(&tv, NULL);
	rawtime = tv.tv_sec;
	timeinfo = localtime (&rawtime);
	double microsec = tv.tv_usec;

	ofstream out;
	out.open(output_file.c_str(), std::ios::app);


	char *timeinfo_after = asctime(timeinfo);
	timeinfo_after[strlen(timeinfo_after) - 1] = 0;
	cout << timeinfo_after << ";" << rawtime << ";" <<  microsec << ";" << hostname_string << display_name << ";" << event_type << ";" << name  << endl;
	if (out.is_open()) {
		// sizeMB is only not empty when the event_type is cached-postload or noncached-postload
		if (sizeMB.empty()){
			out << timeinfo_after << ";" << rawtime << ";" <<  microsec << ";" << hostname_string << display_name << ";" << event_type << ";" << name << "\n";
		}else{
			out << timeinfo_after << ";" << rawtime << ";" <<  microsec << ";" << hostname_string << display_name << ";" << event_type << ";" << name << ";" << sizeMB << "MB" << "\n";
		}
	}else{
		cout << "problem with opening the file" << endl;
	}
}

protected:
	char hostname[32];
	int id;
	bool loadFull;
	bool loadPart;
	bool loadEvent;
	string event_name;
	char* display_name;
	char* filename;
};




int main( int argc, char **argv )
{



	// The first argument to the program tells us which of the known VR
	// setups to start
	std::string setupStr;
	MyVRApp *app;

	if (argc >= 2)
	{
		setupStr = std::string(argv[1]);
	}

	// This opens up the graphics window, and starts connections to
	// input devices, but doesn't actually start rendering yet.

	app = new MyVRApp(setupStr, argv[2]);

	// This starts the rendering/input processing loop
	app->run();

	return 0;
}


//
////////////////////  end  common/vrg3d/demo/vrg3d_demo.cpp  ///////////////////
