#include <iostream>     // std::cout
#include <fstream>      // std::ifstream
#include <vector> 
#include <sys/time.h>
#include <stdlib.h>
#include <string.h>

using namespace std;
int main( int argc, const char* argv[] )
{


	streampos size;
	char * memblock;

	//read file 
	ifstream file (argv[1], ios::in|ios::binary|ios::ate);
	int division = 1;
	if(argc > 2){
		division = atoi(argv[2]);
	}
	int part = 0;
	if(argc > 3){
		part = atoi(argv[3]) - 1;
	}
	
	if (file.is_open())
	{
		size = file.tellg();
		int newSize = size / division;
		
		memblock = new char [newSize];
		file.seekg (newSize * part, ios::beg);
		
		struct timeval diff, startTV, endTV;
		gettimeofday(&startTV, NULL); 
		
		file.read (memblock, newSize);
		
		gettimeofday(&endTV, NULL); 
		timersub(&endTV, &startTV, &diff);
		
		file.close();

		double sizeMB = ((double) newSize) / 1024.0 / 1024.0;
		double timeSec = 0.000001 * diff.tv_usec + diff.tv_sec;

		cout << "the entire file content is in memory - Size " <<  sizeMB << " MB" << std::endl;
		cout << "time taken = " <<  timeSec << "sec" << std::endl;
		cout << sizeMB / timeSec  << " MB/s" << std::endl; 

		delete[] memblock;
	}
	else cout << "Unable to open file";
	return 0;
}